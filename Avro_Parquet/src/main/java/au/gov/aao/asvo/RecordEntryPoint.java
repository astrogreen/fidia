package au.gov.aao.asvo;

/**
 * Created by lharischandra on 27/01/2016.
 */
import com.google.common.primitives.Bytes;
import org.apache.avro.Schema;
import org.apache.avro.generic.GenericData;
import org.apache.avro.generic.GenericRecord;
import org.apache.hadoop.fs.Path;
import org.apache.parquet.avro.AvroParquetWriter;
import py4j.GatewayServer;

import java.io.*;
import java.util.*;
import java.lang.Math;
// import java.util.Arrays;
// import java.util.List;
// import java.util.Collection;
import java.nio.ByteBuffer;
import java.nio.IntBuffer;
import java.nio.DoubleBuffer;
import java.nio.LongBuffer;
import java.nio.ByteOrder;


public class RecordEntryPoint {

    // List<AstroObjRecord> records = new ArrayList<AstroObjRecord>();

    static Schema.Parser parser = new Schema.Parser();

    // public AstroObjRecord getRecord(String id) {
    //     return new AstroObjRecord(id);
    // }

    // public Trait getTrait(String type){
    //     return new Trait(type);
    // }

    // /**
    //  * When we add record, we should actually add it to a datum array
    //  * which then will be written out
    //  * @param r
    //  */
    // public void addRecord(AstroObjRecord r){
    //     records.add(r);
    // }

    /**
     * Well actually let's create a AvroParquetWriter here and send it to python.
     * Python will use it to write out datums.
     * @param schema
     */
    public AvroParquetWriter<GenericRecord> getParquetWriter(Schema schema){

        Path path = new Path("file:///home/agreen/sami_test_awg.parquet");
        AvroParquetWriter<GenericRecord> writer = null;
        try {
            writer = new AvroParquetWriter<GenericRecord>(path, schema);


        } catch (IOException e) {
            e.printStackTrace();
        }
        return writer;

    }

    // public DataFileWriter<GenericRecord> getAvroWriter(Schema schema){
    //     String dst = "hdfs://asvotest1.aao.gov.au/user/admin/astro_test2.avro";

    //     Configuration conf = new Configuration();
    //     DataFileWriter<GenericRecord> dataFileWriter = null;
    //     OutputStream out;
    //     try {
    //         FileSystem fs = FileSystem.get(URI.create(dst), conf);
    //         out = fs.create(new Path(dst), new Progressable() {
    //             @Override
    //             public void progress() {
    //                 System.out.print(".");
    //             }
    //         });

    //         DatumWriter<GenericRecord> datumWriter = new GenericDatumWriter<GenericRecord>(schema);
    //         dataFileWriter = new DataFileWriter<GenericRecord>(datumWriter);
    //         dataFileWriter.create(schema, out);
    //     }
    //     catch (IOException e){
    //         e.printStackTrace();
    //     }
    //     return dataFileWriter;
    // }

    /**
     * We also need a schema creator. Now do everything in python side and see what happens.
     * @param schema
     */
    public Schema getSchema(String schema){

        return parser.parse(schema);
//        try {
//            InputStream in = new BufferedInputStream(new FileInputStream(schemaPath));
//            schema = parser.parse(in);
//        } catch (IOException e) {
//            e.printStackTrace();
//        }
//
//        return schema;
    }

    /**
     * You get a generic record here.
     * @param schema
     * @return
     */
    public GenericRecord getDatum(Schema schema){
        GenericRecord d = new GenericData.Record(schema);
        return d;
    }

    public Object getMap(){


        return null;
    }

//    public void testMethod(Schema schema){
//        List<Schema> l = schema.getTypes();
//        Schema.Type.ARRAY;
//        schema.getElementType();
//        schema.getType()
//    }

    /**
     * In case we used byte[] and if they are too big, we have split them from python side
     * and send to java side to merge and put in the astro record.
     * @param datum
     * @param partOne
     * @param partTwo
     * @return
     */
    public GenericRecord mergeBytes(GenericRecord datum, byte[] partOne, byte[] partTwo){

        //byte[] m = Bytes.concat(partOne, partTwo);
        datum.put("value", Bytes.concat(partOne, partTwo));
        return datum;
    }

    /**
     * combineByteList
     *
     * There is a limit to how big a byte array Py4J can handle. To overcome
     * that limit, the byte array must be broken into chunks on the Python
     * side, and then handed to Java one-by-one through the Py4J `ListConvert`
     * mechanism. The resulting list of byte arrays must be re-concatenated
     * in Java, which is what this function does.
     */
    private static byte[] combineByteList(List<byte[]> byteList, int totalSize, int chunkSize){
        /* Byte array big enough to hold full output */
        byte[] combinedBytes = new byte[totalSize];

        /* Variable to track offset within the output byte array */
        int offset = 0;

        /* Loop over the input list of byte arrays and copy each into the output byte array */
        for (int i=0; i < byteList.size(); i++) {
            int end_offset = Math.min(offset + chunkSize, totalSize);
            System.arraycopy(byteList.get(i), 0, combinedBytes, offset, end_offset);
            offset += chunkSize;
        }
        return combinedBytes;
    }

    private static List<Double> convertByteArrayToDoubleList(byte[] byteArray, String endian) {
        /* ByteBuffer: https://docs.oracle.com/javase/7/docs/api/java/nio/ByteBuffer.html */
        ByteBuffer byteBuffer = ByteBuffer.wrap(byteArray);
        if (endian.equals("<")) {
            /* Input is not Java native big endian. */
            System.out.println("Changing byte order to little endian");
            byteBuffer.order(ByteOrder.LITTLE_ENDIAN);
        }

        /* Consider also using ByteBuffer.getDouble */
        DoubleBuffer doubleBuffer = byteBuffer.asDoubleBuffer();
        int size = doubleBuffer.remaining();
        List<Double> outList = new ArrayList(size);
        for (int i=0; i < size; i++) {
            outList.add(doubleBuffer.get());
        }
        return outList;
    }

    private static List<Integer> convertByteArrayToIntegerList(byte[] byteArray, String endian) {
        /* ByteBuffer: https://docs.oracle.com/javase/7/docs/api/java/nio/ByteBuffer.html */
        ByteBuffer byteBuffer = ByteBuffer.wrap(byteArray);
        if (endian.equals("<")) {
            /* Input is not Java native big endian. */
            System.out.println("Changing byte order to little endian");
            byteBuffer.order(ByteOrder.LITTLE_ENDIAN);
        }
        IntBuffer intBuffer = byteBuffer.asIntBuffer();
        int size = intBuffer.remaining();
        List<Integer> outList = new ArrayList(size);
        for (int i=0; i < size; i++) {
            outList.add(intBuffer.get());
        }
        return outList;
    }

    private static List<Long> convertByteArrayToLongList(byte[] byteArray, String endian) {
        /* ByteBuffer: https://docs.oracle.com/javase/7/docs/api/java/nio/ByteBuffer.html */
        ByteBuffer byteBuffer = ByteBuffer.wrap(byteArray);
        if (endian.equals("<")) {
            /* Input is not Java native big endian. */
            System.out.println("Changing byte order to little endian");
            byteBuffer.order(ByteOrder.LITTLE_ENDIAN);
        }
        LongBuffer longBuffer = byteBuffer.asLongBuffer();
        int size = longBuffer.remaining();
        List<Long> outList = new ArrayList(size);
        for (int i=0; i < size; i++) {
            outList.add(longBuffer.get());
        }
        return outList;
    }

    /**
     * integerListFromSplitByteArray combines the tasks of recombining a list 
     * of bytes arrays provided from Python and converting it into a Java 
     * list. These steps must be combined in Java, otherwise Py4J simply tries
     * to copy the byte array back to Python.
     */
    public static List<Integer> integerListFromSplitByteArray(List<byte[]> byteList, int totalSize, int chunkSize, String endian) {
        byte[] combinedBytes = combineByteList(byteList, totalSize, chunkSize);
        return convertByteArrayToIntegerList(combinedBytes, endian);
    }

    /**
     * doubleListFromSplitByteArray combines the tasks of recombining a list 
     * of bytes arrays provided from Python and converting it into a Java 
     * list. These steps must be combined in Java, otherwise Py4J simply tries
     * to copy the byte array back to Python.
     */
    public static List<Double> doubleListFromSplitByteArray(List<byte[]> byteList, int totalSize, int chunkSize, String endian) {
        byte[] combinedBytes = combineByteList(byteList, totalSize, chunkSize);
        return convertByteArrayToDoubleList(combinedBytes, endian);
    }

    public static List<Long> longListFromSplitByteArray(List<byte[]> byteList, int totalSize, int chunkSize, String endian) {
        byte[] combinedBytes = combineByteList(byteList, totalSize, chunkSize);
        return convertByteArrayToLongList(combinedBytes, endian);
    }

    public static void main(String[] args) {
        GatewayServer gatewayServer = new GatewayServer(new RecordEntryPoint());
        gatewayServer.start();
        System.out.println("Gateway Server Started");
        long maxheap = Runtime.getRuntime().maxMemory();
        System.out.println("Max heap " + maxheap);
    }
}
