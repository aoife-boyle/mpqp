from typing import Optional, Union

import numpy as np
from qiskit import QuantumCircuit, transpile
from qiskit.circuit import CircuitInstruction

from mpqp.core.circuit import QCircuit
from mpqp.core.instruction.gates.gate import SingleQubitGate
from mpqp.core.instruction.gates.native_gates import (
    NATIVE_GATES,
    TOF,
    CRk,
    NativeGate,
    P,
    Rk,
    RotationGate,
    Rx,
    Ry,
    Rz,
    U,
)
from mpqp.core.instruction.gates.parametrized_gate import ParametrizedGate
from mpqp.tools.maths import closest_unitary


def random_circuit(
    gate_classes: Optional[list[type]] = None,
    nb_qubits: int = 5,
    nb_gates: Optional[int] = None,
    seed: Optional[Union[int, np.random.Generator]] = None,
):
    """This function creates a QCircuit with a specified number of qubits and gates.
    The gates are chosen randomly from the provided list of native gate classes.

    args:
        nb_qubits : Number of qubits in the circuit.
        gate_classes : List of native gate classes to use in the circuit.
        nb_gates : Number of gates to add to the circuit.
        seed: Seed used to control the random generation of the circuit.

    Returns:
        A quantum circuit with the specified number of qubits and randomly chosen gates.

    Raises:
        ValueError: If the number of qubits is too low for the specified gates.

    Examples:
        >>> random_circuit([U, TOF], 3)
                                          ┌───┐          ┌─────────────────────────┐
        q_0: ─────────────────────────────┤ X ├──■────■──┤ U(2.8347,3.0652,3.7577) ├
             ┌───────────────────────────┐└─┬─┘  │    │  ├─────────────────────────┤
        q_1: ┤ U(3.6779,1.1801,0.037754) ├──■────■────■──┤ U(3.0549,3.3383,4.1652) ├
             └───────────────────────────┘  │  ┌─┴─┐┌─┴─┐├─────────────────────────┤
        q_2: ───────────────────────────────■──┤ X ├┤ X ├┤ U(5.0316,3.0011,4.0064) ├
                                               └───┘└───┘└─────────────────────────┘

        >>> from mpqp.core.instruction.gates import native_gates
        >>> random_circuit(native_gates.NATIVE_GATES, 4, 10)
                                             ┌───┐┌───┐  ┌───┐  ┌───────┐
        q_0: ────────────────────────────────┤ X ├┤ X ├──┤ Z ├──┤ Rz(5) ├─X─
             ┌───┐                           └─┬─┘└─┬─┘  └───┘  └───────┘ │
        q_1: ┤ S ├─────────────────────────────■────┼─────────────────────┼─
             ├───┤┌─────────────────────────┐  │    │                     │
        q_2: ┤ Z ├┤ U(4.4304,2.9725,1.8644) ├──■────┼─────────────────────X─
             └───┘└─────────────────────────┘       │  ┌───────┐  ┌───┐
        q_3: ───────────────────────────────────────■──┤ Ry(4) ├──┤ S ├─────
                                                       └───────┘  └───┘

        >>> print(random_circuit([U, TOF], 3, seed=123)) # doctest: +NORMALIZE_WHITESPACE
                  ┌───┐                           ┌───┐
        q_0: ──■──┤ X ├───────────────────────────┤ X ├
             ┌─┴─┐└─┬─┘┌─────────────────────────┐└─┬─┘
        q_1: ┤ X ├──■──┤ U(5.1025,5.8015,1.7378) ├──■──
             └─┬─┘  │  ├─────────────────────────┤  │
        q_2: ──■────■──┤ U(5.5914,3.2231,1.5392) ├──■──
                       └─────────────────────────┘

        >>> from mpqp.core.instruction.gates import native_gates
        >>> print(random_circuit(native_gates.NATIVE_GATES, 4, 10, seed=123)) # doctest: +NORMALIZE_WHITESPACE
                                  ┌───┐           ┌────────┐┌───┐┌───┐
        q_0: ───────■─────────────┤ I ├───────────┤ P(π/4) ├┤ Y ├┤ X ├
                    │  ┌──────────┴───┴──────────┐├───────┬┘├───┤└─┬─┘
        q_1: ──■────┼──┤ U(1.7378,5.1507,5.5914) ├┤ Rz(5) ├─┤ H ├──■──
             ┌─┴─┐  │  └─────────────────────────┘└───────┘ └───┘  │
        q_2: ┤ X ├──┼──────────────────────────────────────────────■──
             └───┘┌─┴─┐           ┌───┐
        q_3: ─────┤ X ├───────────┤ I ├───────────────────────────────
                  └───┘           └───┘

    """
    if seed is None:
        rng = np.random.default_rng()
    elif isinstance(seed, np.random.Generator):
        rng = seed
    else:
        rng = np.random.default_rng(seed)

    if gate_classes is None:
        gate_classes = NATIVE_GATES

    if nb_gates is None:
        nb_gates = rng.integers(5, 10)

    qubits = list(range(nb_qubits))
    qcircuit = QCircuit(nb_qubits)

    if any(
        not issubclass(gate, SingleQubitGate)
        and ((gate == TOF and nb_qubits <= 2) or nb_qubits <= 1)
        for gate in gate_classes
    ):
        raise ValueError("number of qubits too low for this gates")

    for _ in range(nb_gates):
        gate_class: type[NativeGate] = rng.choice(gate_classes)  # type: ignore[reportArgumentType]
        target = int(rng.choice(qubits))
        if issubclass(gate_class, SingleQubitGate):
            if issubclass(gate_class, ParametrizedGate):
                if issubclass(gate_class, U):
                    qcircuit.add(
                        gate_class(
                            rng.uniform(0, 2 * np.pi),
                            rng.uniform(0, 2 * np.pi),
                            rng.uniform(0, 2 * np.pi),
                            target,
                        )
                    )
                elif issubclass(gate_class, Rk):
                    qcircuit.add(Rk(rng.integers(1, 10), target))
                elif issubclass(gate_class, RotationGate):
                    if TYPE_CHECKING:
                        assert issubclass(gate_class, (Rx, Ry, Rz, P))
                    qcircuit.add(gate_class(random.uniform(0, 2 * np.pi), target))
                else:
                    qcircuit.add(gate_class(int(rng.uniform(0, 2 * np.pi)), target))  # type: ignore[reportArgumentType]
                    raise ValueError
            else:
                qcircuit.add(gate_class(target))
        else:
            control = int(rng.choice(list(set(qubits) - {target})))
            if issubclass(gate_class, ParametrizedGate):
                if TYPE_CHECKING:
                    assert issubclass(gate_class, CRk)
                qcircuit.add(gate_class(rng.integers(0, 10), control, target))  # type: ignore[reportArgumentType]
            elif issubclass(gate_class, TOF):
                control2 = int(rng.choice(list(set(qubits) - {target, control})))
                qcircuit.add(TOF([control, control2], target))
            else:
                qcircuit.add(gate_class(control, target))
    return qcircuit


def compute_expected_matrix(qcircuit: QCircuit):
    """
    Computes the expected matrix resulting from applying single-qubit gates
    in reverse order on a quantum circuit.

    args:
        qcircuit : The quantum circuit object containing instructions.

    returns:
        Expected matrix resulting from applying the gates.

    raises:
        ValueError: If any gate in the circuit is not a SingleQubitGate.
    """
    from sympy import N

    from mpqp.core.instruction.gates.gate import Gate, SingleQubitGate

    gates = [
        instruction
        for instruction in qcircuit.instructions
        if isinstance(instruction, Gate)
    ]
    nb_qubits = qcircuit.nb_qubits

    result_matrix = np.eye(2**nb_qubits, dtype=complex)

    for gate in reversed(gates):
        if not isinstance(gate, SingleQubitGate):
            raise ValueError(
                f"Unsupported gate: {type(gate)} only SingleQubitGate can be computed for now"
            )
        matrix = np.eye(2**nb_qubits, dtype=complex)
        gate_matrix = gate.to_matrix()
        index = gate.targets[0]
        matrix = np.kron(
            np.eye(2**index, dtype=complex),
            np.kron(gate_matrix, np.eye(2 ** (nb_qubits - index - 1), dtype=complex)),
        )

        result_matrix = np.dot(result_matrix, matrix)

    return np.vectorize(N)(result_matrix).astype(complex)


def replace_custom_gate(
    custom_unitary: CircuitInstruction, nb_qubits: int
) -> tuple[QuantumCircuit, float]:
    """Decompose and replace the (custom) qiskit unitary given in parameter by a
    qiskit `QuantumCircuit` composed of ``U`` and ``CX`` gates.

    Note:
        When using Qiskit, a global phase is introduced (related to usage of
        ``u`` in OpenQASM2). This may be problematic in some cases, so this
        function also returns the global phase introduced so it can be corrected
        later on.

    Args:
        custom_unitary: instruction containing the custom unitary operator.
        nb_qubits: Number of qubits of the circuit from which the unitary
            instruction was taken.

    Returns:
        A circuit containing the decomposition of the unitary in terms
        of gates ``U`` and ``CX``, and the global phase used to
        correct the statevector if need be.
    """
    from qiskit.exceptions import QiskitError

    transpilation_circuit = QuantumCircuit(nb_qubits)
    transpilation_circuit.append(custom_unitary)
    try:
        transpiled = transpile(transpilation_circuit, basis_gates=['u', 'cx'])
    except QiskitError as e:
        # if the error is arising from TwoQubitWeylDecomposition, we replace the
        # matrix by the closest unitary
        if "TwoQubitWeylDecomposition" in str(e):
            custom_unitary.operation.params[0] = closest_unitary(
                custom_unitary.operation.params[0]
            )
            transpiled = transpile(transpilation_circuit, basis_gates=['u', 'cx'])
        else:
            raise e
    return transpiled, transpiled.global_phase
