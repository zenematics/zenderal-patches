using System.Text.Json;
using System.Text.Json.Nodes;

namespace MagicExtract;

public static class Json
{
    public static readonly JsonSerializerOptions Options = new()
    {
        WriteIndented = true,
        PropertyNamingPolicy = JsonNamingPolicy.CamelCase,
        DefaultIgnoreCondition = System.Text.Json.Serialization.JsonIgnoreCondition.WhenWritingNull,
    };

    public static JsonObject ToNode<T>(T dto)
        => (JsonObject)JsonSerializer.SerializeToNode(dto, Options)!;

    public static void WriteFile(string path, object payload)
    {
        Directory.CreateDirectory(Path.GetDirectoryName(path)!);
        File.WriteAllText(path, JsonSerializer.Serialize(payload, Options) + "\n");
    }
}
