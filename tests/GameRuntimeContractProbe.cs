using System;
using System.IO;
using System.Linq;
using System.Reflection;
using System.Runtime.Serialization;
using System.Text;
using System.Xml;
using RoadtripKoreanFontBridge;

// Runs managed, non-Unity-native methods from the user's own DLL. It never
// launches the game, writes saves, or includes game code in the repository.
internal static class GameRuntimeContractProbe
{
    private const BindingFlags All = BindingFlags.Public | BindingFlags.NonPublic | BindingFlags.Static | BindingFlags.Instance;
    public static void Main(string[] args)
    {
        string managed = Path.Combine(args[0], "MonsterRoadtrip_Data", "Managed");
        AppDomain.CurrentDomain.AssemblyResolve += (_, e) => {
            string path = Path.Combine(managed, new AssemblyName(e.Name).Name + ".dll");
            return File.Exists(path) ? Assembly.LoadFrom(path) : null;
        };
        Assembly game = Assembly.LoadFrom(Path.Combine(managed, "Assembly-CSharp.dll"));
        Type crypto = game.GetType("BeautifulGlitch.CryptoUtils", true);
        Type serializer = game.GetType("BeautifulGlitch.CoreCheckpointXmlSerializer", true);
#pragma warning disable SYSLIB0050
        object serializerInstance = FormatterServices.GetUninitializedObject(serializer);
#pragma warning restore SYSLIB0050
        MethodInfo read = game.GetType("BeautifulGlitch.XmlSerializer", true).GetMethod(
            "UnserializeString", All, null, new[] { typeof(XmlNode), typeof(string), typeof(string) }, null);
        foreach (string name in new[] { "재클린", "Jacqueline", "한글<&이름", "여행자🚗" })
        {
            using (MemoryStream stream = new MemoryStream())
            using (XmlTextWriter writer = new XmlTextWriter(stream, new ASCIIEncoding()))
            {
                writer.WriteStartElement("CorePlayerData");
                SaveNameEncoding.WriteElementString(writer, "Name", name);
                writer.WriteEndElement(); writer.Flush();
                XmlDocument before = new XmlDocument();
                before.LoadXml(Encoding.ASCII.GetString(stream.ToArray()));
                string encrypted = (string)crypto.GetMethod("Encrypt", All).Invoke(null, new object[] { before.DocumentElement.InnerXml });
                string decrypted = (string)crypto.GetMethod("Decrypt", All).Invoke(null, new object[] { encrypted });
                XmlDocument after = new XmlDocument(); after.LoadXml("<CorePlayerData>" + decrypted + "</CorePlayerData>");
                string restored = (string)read.Invoke(serializerInstance, new object[] { after.DocumentElement, "Name", "MISSING" });
                if (restored != name) throw new Exception("Original DLL crypto/name reader round-trip failed");
            }
        }
        Console.WriteLine("PASS original DLL Encrypt/Decrypt + UnserializeString: 4 Unicode name round-trips");

        Type statType = game.GetType("BeautifulGlitchConfig.StatType", true);
        MethodInfo check = game.GetType("BeautifulGlitch.MultiAlwaysSucceedEventParser", true).GetMethod("CheckStat", All);
        Func<string, string, bool, bool> hasStat = (text, stat, positive) => {
            object[] values = { text, Enum.Parse(statType, stat), positive, (uint)0 };
            return (bool)check.Invoke(null, values) && (uint)values[3] == 2;
        };
        if (hasStat("+N2 STAMINA을 얻는다", "Stamina", true)) throw new Exception("Expected original Hangul boundary failure");
        if (!hasStat("+N2 STAMINA\u200b을 얻는다", "Stamina", true)) throw new Exception("Boundary repair failed original DLL CheckStat");
        string[] lines = File.ReadAllLines(args[1]);
        int start = Array.FindIndex(lines, line => line.Split('\t').Take(2).SequenceEqual(new[] { ">>>", "evilmenu" }));
        if (start < 0) throw new Exception("evilmenu missing");
        int end = Array.FindIndex(lines, start + 1, line => line.StartsWith(">>>\t"));
        if (end < 0) end = lines.Length;
        string[] block = lines.Skip(start).Take(end - start).ToArray();
        int outcome = Array.FindIndex(block, line => line == ">outcome\t3");
        string text3 = string.Join("\n", block.Skip(outcome + 1).Where(l => l.StartsWith("\t")).Select(l => l.Split('\t')[3]));
        if (outcome < 0 || !hasStat(text3, "Stamina", true) || !hasStat(text3, "Hype", false))
            throw new Exception("evilmenu outcome 3 fails original DLL stat checks");
        int locationCount = lines.Count(line => line == ">location\tdiner_doom");
        if (locationCount != 3) throw new Exception("diner_doom raw location count is " + locationCount);
        Console.WriteLine("PASS original DLL CheckStat: reproduced boundary failure, repaired boundary, evilmenu outcome 3; diner_doom raw definitions=3");
    }
}
