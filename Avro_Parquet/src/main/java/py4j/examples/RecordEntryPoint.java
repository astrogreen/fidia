package py4j.examples;

/**
 * Created by lharischandra on 27/01/2016.
 */
import com.google.common.primitives.Bytes;
import org.apache.avro.Schema;
import org.apache.avro.file.DataFileWriter;
import org.apache.avro.generic.GenericData;
import org.apache.avro.generic.GenericDatumWriter;
import org.apache.avro.generic.GenericRecord;
import org.apache.avro.io.DatumWriter;
import org.apache.hadoop.conf.Configuration;
import org.apache.hadoop.fs.FileSystem;
import org.apache.hadoop.fs.Path;
import org.apache.hadoop.util.Progressable;
import org.apache.parquet.avro.AvroParquetWriter;
import py4j.GatewayServer;

import java.io.*;
import java.net.URI;
import java.util.ArrayList;
import java.util.List;

public class RecordEntryPoint {

    List<AstroObjRecord> records = new ArrayList<AstroObjRecord>();

    static Schema.Parser parser = new Schema.Parser();

    public AstroObjRecord getRecord(String id) {
        return new AstroObjRecord(id);
    }

    public Trait getTrait(String type){
        return new Trait(type);
    }

    /**
     * When we add record, we should actually add it to a datum array
     * which then will be written out
     * @param r
     */
    public void addRecord(AstroObjRecord r){
        records.add(r);
    }

    /**
     * Well actually let's create a AvroParquetWriter here and send it to python.
     * Python will use it to write out datums.
     * @param schema
     */
    public AvroParquetWriter<GenericRecord> getParquetWriter(Schema schema){

        Path path = new Path("hdfs://asvotest1.aao.gov.au/user/admin/Sami_Test/sami_test2.parquet");
        AvroParquetWriter<GenericRecord> writer = null;
        try {
            writer = new AvroParquetWriter<GenericRecord>(path, schema);


        } catch (IOException e) {
            e.printStackTrace();
        }
        return writer;

    }

    public DataFileWriter<GenericRecord> getAvroWriter(Schema schema){
        String dst = "hdfs://asvotest1.aao.gov.au/user/admin/astro_test2.avro";

        Configuration conf = new Configuration();
        DataFileWriter<GenericRecord> dataFileWriter = null;
        OutputStream out;
        try {
            FileSystem fs = FileSystem.get(URI.create(dst), conf);
            out = fs.create(new Path(dst), new Progressable() {
                @Override
                public void progress() {
                    System.out.print(".");
                }
            });

            DatumWriter<GenericRecord> datumWriter = new GenericDatumWriter<GenericRecord>(schema);
            dataFileWriter = new DataFileWriter<GenericRecord>(datumWriter);
            dataFileWriter.create(schema, out);
        }
        catch (IOException e){
            e.printStackTrace();
        }
        return dataFileWriter;
    }

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


    public static void main(String[] args) {
        GatewayServer gatewayServer = new GatewayServer(new RecordEntryPoint());
        gatewayServer.start();
        System.out.println("Gateway Server Started");
        long maxheap = Runtime.getRuntime().maxMemory();
        System.out.println("Max heap " + maxheap);
    }
}
