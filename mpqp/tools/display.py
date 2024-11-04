from __future__ import annotations

import re

import numpy as np
import numpy.typing as npt

from .generics import Matrix


def state_vector_ket_shape(sv: npt.NDArray[np.complex64]) -> str:
    """Formats a state vector into its ket format."""
    if len(sv.shape) != 1:
        raise ValueError(f"Input state {sv} should be a vector (1 dimensional matrix).")
    nb_qubits = int(np.log2(len(sv)))
    if 2**nb_qubits != len(sv):
        raise ValueError(f"Input state {sv} should have a power of 2 size")
    return (
        " ".join(
            f"{with_sign(v)}|{np.binary_repr(i,nb_qubits)}⟩"
            for i, v in enumerate(sv)
            if v.round(3) != 0
        )
    )[2:]


def with_sign(val: np.complex64) -> str:
    """Sometimes, we want values under a specific format, in particular
    ``<sign> <value>``. Where value is as simple as possible (*e.g.* no period
    or no imaginary part if there is no need).

    Args:
        val: The value to be formatted.

    Returns:
        The formatted value
    """
    rounded = _remove_null_imag(val)
    if rounded == 1:
        return "+ "
    if rounded.real == 0:
        sign = "+ " if rounded.imag >= 0 else "- "
        rounded = _remove_unnecessary_decimals(abs(rounded))
        return sign + str(rounded) + "j"
    str_rounded = str(rounded)
    if str_rounded.startswith("-") or str_rounded.startswith("(-"):
        return "- " + str(-rounded)
    return "+ " + str_rounded


def _remove_null_imag(val: np.complex64) -> np.complex64 | np.float32 | int:
    val = np.round(val, 3)
    if val.imag != 0:
        return val
    return _remove_unnecessary_decimals(val.real)


def _remove_unnecessary_decimals(val: np.float32 | int) -> np.float32 | int:
    val = np.float32(val)
    if val.is_integer():
        return int(val)
    return val


def clean_1D_array(
    array: list[complex] | npt.NDArray[np.complex64 | np.float32], round: int = 7
) -> str:
    """Cleans and formats elements of an array.
    This function rounds the real parts of complex numbers in the array to 7 decimal places
    and formats them as integers if they are whole numbers. It returns a string representation
    of the cleaned array without parentheses.

    Args:
        array: An array containing numeric elements, possibly including complex numbers.

    Returns:
        A string representation of the cleaned array without parentheses.

    Example:
        >>> clean_1D_array([1.234567895546, 2.3456789645645, 3.45678945645])
        '[1.2345679, 2.345679, 3.4567895]'
        >>> clean_1D_array([1+2j, 3+4j, 5+6j])
        '[1+2j, 3+4j, 5+6j]'
        >>> clean_1D_array([1+0j, 0+0j, 5.])
        '[1, 0, 5]'
        >>> clean_1D_array([1.0, 2.0, 3.0])
        '[1, 2, 3]'
        >>> clean_1D_array([-0.01e-09+9.82811211e-01j,  1.90112689e-01+5.22320655e-09j,
        ... 2.91896816e-09-2.15963155e-09j, -4.17753839e-09-5.64638430e-09j,
        ... 9.44235988e-08-8.58300965e-01j, -5.42123454e-08+2.07957438e-07j,
        ... 5.13144658e-01+2.91786504e-08j, -0000000.175980538-1.44108434e-07j])
        '[0.9828112j, 0.1901127, 0, 0, 1e-07-0.858301j, -1e-07+2e-07j, 0.5131446, -0.1759805-1e-07j]'

    """
    array = np.array(array, dtype=np.complex64)
    cleaned_array = []
    for element in array:
        real_part = np.round(np.real(element), round)
        imag_part = np.round(np.imag(element), round)

        if real_part == int(real_part):
            real_part = int(real_part)
        if imag_part == int(imag_part):
            imag_part = int(imag_part)

        if real_part == 0 and imag_part != 0:
            real_part = ""

        if imag_part == 0:
            imag_part = ""
        else:
            imag_part = str(imag_part) + "j"
            if real_part != "" and not imag_part.startswith("-"):
                imag_part = "+" + imag_part

        cleaned_array.append(f"{str(real_part)}{str(imag_part)}")

    return "[" + ", ".join(map(str, cleaned_array)) + "]"


def clean_matrix(matrix: Matrix):
    """Cleans and formats elements of a matrix.
    This function cleans and formats the elements of a matrix. It rounds the real parts of complex numbers
    in the matrix to 7 decimal places and formats them as integers if they are whole numbers. It returns a
    string representation of the cleaned matrix without parentheses.

    Args:
        matrix: A matrix containing numeric elements, possibly including complex numbers.

    Returns:
        str: A string representation of the cleaned matrix without parentheses.

    Examples:
        >>> print(clean_matrix([[1.234567895546, 2.3456789645645, 3.45678945645],
        ...               [1+0j, 0+0j, 5.],
        ...               [1.0, 2.0, 3.0]]))
        [[1.2345679, 2.345679, 3.4567895],
         [1, 0, 5],
         [1, 2, 3]]

    """
    # TODO: add an option to align cols
    cleaned_matrix = [clean_1D_array(row) for row in matrix]
    return "[" + ",\n ".join(cleaned_matrix) + "]"


def pprint(matrix: Matrix):
    print(clean_matrix(matrix))


def one_lined_repr(obj: object):
    """One-liner returning a representation of the given object by removing
    extra whitespace.

    Args:
        obj: The object for which a representation is desired.
    """
    return re.sub(r"\s+", " ", repr(obj))