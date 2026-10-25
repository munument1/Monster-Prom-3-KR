using System;
using System.Reflection;
using System.Runtime.CompilerServices;
using System.Runtime.InteropServices;
using HarmonyLib;
using System.Collections.Generic;
using RoadtripKoreanFontBridge;

public static class MonoShutdownProbe
{
    [MethodImpl(MethodImplOptions.NoInlining)]
    public static int Target() { return 5; }
    public static void Postfix(ref int __result) { __result += 2; }
    public static void RunPatch()
    {
        Harmony harmony = new Harmony("roadtrip.isolated.shutdown.probe");
        harmony.Patch(
            typeof(MonoShutdownProbe).GetMethod("Target"),
            postfix: new HarmonyMethod(typeof(MonoShutdownProbe).GetMethod("Postfix")));
        Console.WriteLine("PATCH_RESULT=" + Target());
        if (Environment.GetEnvironmentVariable("ROADTRIP_SHUTDOWN_PROBE").Contains("unpatch"))
        {
            harmony.UnpatchSelf();
            Console.WriteLine("UNPATCH_RESULT=" + Target());
        }
    }
    public static int Main()
    {
        Console.WriteLine("PROBE_START");
        if (Environment.GetEnvironmentVariable("ROADTRIP_SHUTDOWN_PROBE") == "roadmap")
        {
            RunRoadmapPatch();
        }
        if (Environment.GetEnvironmentVariable("ROADTRIP_SHUTDOWN_PROBE") == "corlib")
        {
            Assembly assembly = typeof(MonoShutdownProbe).Assembly;
            IntPtr pointer = (IntPtr)assembly.GetType().GetField("_mono_assembly", BindingFlags.Instance | BindingFlags.NonPublic).GetValue(assembly);
            Console.WriteLine("POINTER_4C_BEFORE=" + Marshal.ReadInt32(pointer, 0x4c).ToString("X8"));
            MonoMod.Utils.Extensions.SetMonoCorlibInternal(assembly, true);
            Console.WriteLine("POINTER_4C_AFTER=" + Marshal.ReadInt32(pointer, 0x4c).ToString("X8"));
            Console.WriteLine("CORLIB_53=" + Marshal.ReadByte(pointer, 0x53));
        }
        if ((Environment.GetEnvironmentVariable("ROADTRIP_SHUTDOWN_PROBE") ?? "").StartsWith("harmony")) RunPatch();
        Console.WriteLine("MANAGED_MAIN_COMPLETE");
        return 0;
    }

    public static void RunRoadmapPatch()
    {
        Harmony harmony = new Harmony("roadtrip.isolated.roadmap.probe");
        harmony.Patch(typeof(RoadmapMarkerProbe).GetMethod("MoveAlongPath"),
            prefix: new HarmonyMethod(typeof(RoadmapMovementFix).GetMethod("BeginPath")));
        List<object> path = new List<object>();
        for (int i = 0; i < 12; i++) path.Add(new object());
        foreach (int previous in new[] { -1, 0, 9 })
        {
            RoadmapMarkerProbe marker = new RoadmapMarkerProbe(previous);
            marker.MoveAlongPath(path, 0, 1f);
            if (marker.ObservedIndex != 0) throw new Exception("New valid path did not reset its section index");
            // The reported failure skipped to point 10 on a 12-point path.
            // All completed section pairs must be addressable after reset.
            for (int section = marker.ObservedIndex; section < 10; section++)
                if (section < 0 || section + 1 >= path.Count) throw new Exception("Invalid section pair");
        }
        RoadmapMarkerProbe invalid = new RoadmapMarkerProbe(-1);
        invalid.MoveAlongPath(null, 0, 1f);
        if (invalid.ObservedIndex != -1) throw new Exception("Null-path handling changed");
        invalid.MoveAlongPath(new List<object> { new object() }, 0, 1f);
        if (invalid.ObservedIndex != -1) throw new Exception("Short-path handling changed");
        harmony.UnpatchSelf();
        RoadmapMarkerProbe original = new RoadmapMarkerProbe(-1);
        original.MoveAlongPath(path, 0, 1f);
        if (original.ObservedIndex != -1) throw new Exception("Unpatch did not restore baseline");
        Console.WriteLine("ROADMAP_CASES=6; valid path reset, invalid paths preserved, unpatch restored");
    }
}

public sealed class RoadmapMarkerProbe
{
    private int mCurrentPointIndex;
    public int ObservedIndex;
    public RoadmapMarkerProbe(int previous) { mCurrentPointIndex = previous; }
    [MethodImpl(MethodImplOptions.NoInlining)]
    public bool MoveAlongPath(List<object> path, int color, float duration)
    {
        ObservedIndex = mCurrentPointIndex;
        return path != null && path.Count >= 2;
    }
}
