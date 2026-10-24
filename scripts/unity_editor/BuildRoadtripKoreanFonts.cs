// Editor-only file. Never compile or load this script in the player's game.
// Run with Unity Editor 2021.3.15f1 to make a Roadtrip-compatible Font bundle.
using System;
using System.IO;
using UnityEditor;
using UnityEngine;

public static class RoadtripFontBundleBuild
{
    public static void Build()
    {
        const string BundleName = "roadtrip_korean_fonts.bundle";
        string[] fontPaths =
        {
            "Assets/KoreanFonts/Jua.ttf",
            "Assets/KoreanFonts/GamjaFlower.ttf",
        };
        foreach (string path in fontPaths)
        {
            if (!File.Exists(path))
                throw new FileNotFoundException("Local-only font not prepared: " + path);
            AssetDatabase.ImportAsset(path, ImportAssetOptions.ForceSynchronousImport);
            var importer = AssetImporter.GetAtPath(path);
            if (importer == null)
                throw new Exception("Font asset importer not found: " + path);
            importer.assetBundleName = BundleName;
        }
        AssetDatabase.SaveAssets();

        string destination = Environment.GetEnvironmentVariable("ROADTRIP_FONT_BUNDLE_OUT");
        if (string.IsNullOrWhiteSpace(destination))
            throw new Exception("ROADTRIP_FONT_BUNDLE_OUT environment variable is required");
        destination = Path.GetFullPath(destination);
        Directory.CreateDirectory(destination);

        AssetBundleManifest manifest = BuildPipeline.BuildAssetBundles(
            destination,
            BuildAssetBundleOptions.ChunkBasedCompression | BuildAssetBundleOptions.StrictMode,
            BuildTarget.StandaloneWindows);
        if (manifest == null || !File.Exists(Path.Combine(destination, BundleName)))
            throw new Exception("Font AssetBundle build returned no output");

        Debug.Log("Korean font AssetBundle built successfully: " + Path.Combine(destination, BundleName));
    }
}
