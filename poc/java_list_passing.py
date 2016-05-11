import sys
import subprocess
from time import sleep

from py4j.java_gateway import JavaGateway, GatewayParameters
from py4j.java_collections import MapConverter, ListConverter
import numpy as np

def byte_array_split(byte_array, max_transfer_block_size):
    """An iterator which returns the byte array in chunks no larger than max_transfer_block_size."""
    for offset_block_index in range(len(byte_array) // max_transfer_block_size):
        offset_block_end_index = min(offset_block_index + max_transfer_block_size, len(byte_array))
        yield byte_array[offset_block_index:offset_block_end_index]

def check_ndarray_equals_javaArray(ndarray, java_array):
    for i in range(len(ndarray)):
        java_value = java_list.get(i)
        print(i, java_value)
        if java_value != ndarray[i]:
            print("Error: Java value '{}' does not match numpy value '{}'".format(
                java_value, ndarray[i]))


def get_endianness(arr):
    if arr.dtype.byteorder == '=':
        if sys.byteorder == 'little':
            byteorder = '<' 
        else:
            byteorder = '>'
    elif arr.dtype.byteorder == '|':
        byteorder = '>'
    else:
        byteorder = arr.dtype.byteorder
    return byteorder

# Start the Java Gateway server

java_process = subprocess.Popen(
    ['java', '-jar', 
    '/home/agreen/asvo/code/all_mirror/Avro_Parquet/target/avro_parquet_1.0-1.0-SNAPSHOT-jar-with-dependencies.jar'])
sleep(2)

try:
    print("Creating gateway connection...")
    gateway = JavaGateway()

    # Create the numpy array:
    arr = np.array([1,2,3], dtype=np.int32)

    # Determine endian-ness:
    byteorder = get_endianness(arr)

    byte_array = arr.tobytes()

    print("Simple conversion of ints")
    java_list = gateway.entry_point.convertByteArrayToIntegerList(byte_array, byteorder)

    print(java_list.toString())

    check_ndarray_equals_javaArray(arr, java_list)

    max_transfer_block_size = 1024**2

    byte_array = arr.tobytes()
    size = len(byte_array)

    java_byte_list = ListConverter().convert([byte_array], gateway._gateway_client)

    print("General conversion of ints")
    java_list = gateway.entry_point.integerListFromSplitByteArray(
        java_byte_list, 
        size, 
        max_transfer_block_size,
        byteorder)

    check_ndarray_equals_javaArray(arr, java_list)

    print("Test of double array")
    # Create the numpy array:
    arr = np.empty((10), dtype=np.float64)

    byte_array = arr.tobytes()
    size = len(byte_array)

    # Determine endian-ness:
    byteorder = get_endianness(arr)

    java_list = gateway.entry_point.doubleListFromSplitByteArray(
        ListConverter().convert([byte_array], gateway._gateway_client), 
        size, 
        max_transfer_block_size,
        byteorder)

    check_ndarray_equals_javaArray(arr, java_list)


finally:
    print("Closing JAVA")
    gateway.shutdown()
    print("Killing java")
    java_process.kill()
    pass
