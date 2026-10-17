using HKX2E;
// usage: hkxconv <in.hkx> <out.xml> | --meta <in.hkx> <out.xml> (Pandora template, keeps node names) | --tohkx <in.xml> <out.hkx>
if (args[0] == "--tohkx") {
    var xd = new HavokXmlDeserializer();
    IHavokObject root;
    using (var rs = File.OpenRead(args[1])) root = xd.Deserialize(rs, HKXHeader.SkyrimSE());
    using var ws = File.Create(args[2]);
    new PackFileSerializer().Serialize(root, new BinaryWriterEx(ws), HKXHeader.SkyrimSE());
} else if (args[0] == "--meta") {
    var des = new MetaPackFileDeserializer();
    IHavokObject root;
    using (var rs = File.OpenRead(args[1])) root = des.Deserialize(new BinaryReaderEx(rs), true);
    var ser = new HavokXmlMetaDataSerializer();
    ser.ShareContext(des.Context);
    ser.ShareContext((HavokXmlDeserializerContext)des.Context);
    using var ws = File.Create(args[2]);
    ser.Serialize(root, HKXHeader.SkyrimSE(), ws);
} else {
    IHavokObject root;
    using (var rs = File.OpenRead(args[0])) root = new PackFileDeserializer().Deserialize(new BinaryReaderEx(rs), true);
    using var ws = File.Create(args[1]);
    new HavokXmlSerializer().Serialize(root, HKXHeader.SkyrimSE(), ws);
}
