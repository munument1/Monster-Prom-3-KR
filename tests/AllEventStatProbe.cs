using System;
using System.IO;
using System.Linq;
using System.Reflection;
using System.Collections.Generic;
using System.Text.RegularExpressions;

// Compare the stat expressions recognized by the installed game's own regex,
// rather than accepting source-like tokens that its parser would miss.
internal static class AllEventStatProbe
{
    public static void Main(string[] args)
    {
        string managed = Path.Combine(args[0], "MonsterRoadtrip_Data", "Managed");
        AppDomain.CurrentDomain.AssemblyResolve += (_, e) => {
            string p = Path.Combine(managed, new AssemblyName(e.Name).Name + ".dll");
            return File.Exists(p) ? Assembly.LoadFrom(p) : null;
        };
        Assembly game = Assembly.LoadFrom(Path.Combine(managed, "Assembly-CSharp.dll"));
        Type types = game.GetType("BeautifulGlitchConfig.StatType", true);
        MethodInfo getRegex = game.GetType("BeautifulGlitch.RegexUtils", true).GetMethod("GetRegexStat");
        Regex normalize = new Regex(@"^[+-]N?\d+\s*[A-Z]+");
        Regex[] patterns = new[] { "Hype", "Magic", "Mind", "Money", "Soul", "Stamina" }
            .Select(s => (Regex)getRegex.Invoke(null, new[] { Enum.Parse(types, s) })).ToArray();
        Func<string, string[]> tokens = text => patterns.SelectMany(p => p.Matches(text).Cast<Match>())
            .Select(m => normalize.Match(m.Value).Value.Replace(" ", "")).OrderBy(s => s, StringComparer.Ordinal).ToArray();
        int checkedRows = 0, statRows = 0, count = 0;
        List<string> failures = new List<string>();
        foreach (string source in Directory.GetFiles(args[1], "english_events_*.txt"))
        {
            string[] before = File.ReadAllLines(source);
            string[] after = File.ReadAllLines(Path.Combine(args[2], Path.GetFileName(source)));
            if (before.Length != after.Length) throw new Exception("Physical line counts differ");
            for (int i = 0; i < before.Length; i++)
            {
                string[] a = before[i].Split('\t'), b = after[i].Split('\t');
                if (a.Length < 4 || b.Length < 4) continue;
                checkedRows++;
                string[] original = tokens(a[3]), translated = tokens(b[3]);
                if (original.Length > 0) { statRows++; count += original.Length; }
                if (!original.SequenceEqual(translated)) failures.Add(Path.GetFileName(source) + ":" + i + " original=" + string.Join(",", original) + " translated=" + string.Join(",", translated));
            }
        }
        foreach (string failure in failures) Console.WriteLine(failure);
        Console.WriteLine("Original DLL regex audit: rows=" + checkedRows + " stat_rows=" + statRows + " expressions=" + count + " mismatches=" + failures.Count);
        if (failures.Count != 0) Environment.ExitCode = 1;
    }
}
