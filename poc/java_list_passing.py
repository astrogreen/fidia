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


# Start the Java Gateway server

# java_process = subprocess.Popen(
#     ['java', '-jar', 
#     '/home/agreen/asvo/code/all_mirror/Avro_Parquet/target/avro_parquet_1.0-1.0-SNAPSHOT-jar-with-dependencies.jar'])
# sleep(2)

try:
    gateway = JavaGateway()

    # Create the numpy array:
    arr = np.array([1,2,3], dtype='>i4')

    byte_array = arr.tobytes()

    java_list = gateway.entry_point.viewAsIntList(byte_array)


    print(java_list.toString())
    gateway.jvm.System.out.println(java_list.toString())

    for i in range(len(arr)):
        print(i, java_list.get(i))

    max_transfer_block_size = 1024**2



    java_byte_list = ListConverter().convert(
        byte_array_split(byte_array, max_transfer_block_size),
        gateway._gateway_client)

    jl = gateway.entry_point.intListFromByteArray(java_byte_list, len(byte_array), max_transfer_block_size)

finally:
    # java_process.kill()
    pass
