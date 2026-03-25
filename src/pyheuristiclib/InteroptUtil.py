import numpy as np
import System

# Mapping from .NET type to NumPy dtype
_dotnet_to_numpy = {
    'System.Byte': np.uint8,
    'System.SByte': np.int8,
    'System.Int16': np.int16,
    'System.UInt16': np.uint16,
    'System.Int32': np.int32,
    'System.UInt32': np.uint32,
    'System.Int64': np.int64,
    'System.UInt64': np.uint64,
    'System.Single': np.float32,
    'System.Double': np.float64,
    'System.Decimal': np.float64  # Convert to float64 for simplicity
}

_numpy_to_dotnet = {
        np.uint8: System.Byte,
        np.int8: System.SByte,
        np.int16: System.Int16,
        np.uint16: System.UInt16,
        np.int32: System.Int32,
        np.uint32: System.UInt32,
        np.int64: System.Int64,
        np.uint64: System.UInt64,
        np.float32: System.Single,
        np.float64: System.Double,
    }

def numpyToCsArray(np_array):
    """
    Converts a NumPy array of numeric types to a strongly-typed .NET array.

    Args:
        np_array (numpy.ndarray): The NumPy array to convert.

    Returns:
        System.Array: A .NET array of appropriate numeric type.
    """
    dtype = np_array.dtype.type
    dotnet_type = _numpy_to_dotnet.get(dtype)
    if dotnet_type is None:
        raise TypeError(f"Unsupported NumPy dtype: {np_array.dtype}")

    shape = np_array.shape

    # Create an empty .NET array of the appropriate type and shape
    cs_array = System.Array.CreateInstance(dotnet_type, *shape)

    # Flatten the NumPy array and copy values to .NET array via indexing
    for idx, value in np.ndenumerate(np_array):
        cs_array[idx] = dotnet_type(value)

    return cs_array

def csArrayToNumpy(CsArray):
    """
    Converts a .NET System.Array of numeric types to a NumPy array.
    
    Args:
        CsArray (System.Array): A .NET array (e.g., System.Int32[], System.Double[]).
    
    Returns:
        numpy.ndarray: A NumPy array with the equivalent dtype.
    """
    element_type = CsArray.GetType().GetElementType().FullName

    np_dtype = _dotnet_to_numpy.get(element_type)
    if np_dtype is None:
        raise TypeError(f"Unsupported .NET array element type: {element_type}")

    shape = tuple(CsArray.GetLength(i) for i in range(CsArray.Rank))
    return np.fromiter(CsArray, dtype=np_dtype).reshape(shape)