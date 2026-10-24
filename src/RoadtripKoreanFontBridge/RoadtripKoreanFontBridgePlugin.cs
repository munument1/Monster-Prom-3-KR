using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Reflection;
using System.Runtime.InteropServices;
using BepInEx;
using BepInEx.Configuration;
using HarmonyLib;
using UnityEngine;
using UnityEngine.SceneManagement;
using UnityEngine.UI;

namespace RoadtripKoreanFontBridge
{
    [BepInPlugin(PluginGuid, PluginName, PluginVersion)]
    public sealed class RoadtripKoreanFontBridgePlugin : BaseUnityPlugin
    {
        public const string PluginGuid = "munument1.roadtrip.koreanfontbridge";
        public const string PluginName = "Monster Roadtrip Korean Font/UI Bridge";
        public const string PluginVersion = "0.1.0";

        private const string DefaultRoadtripBundlePath = @"D:\Codex_Trans\Monster-Prom-3-KR\build\fontbundles\roadtrip_korean_fonts.bundle";
        private const string DefaultLocalFontDirectory = @"D:\Codex_Trans\Monster-Prom-3-KR\work\fonts";
        private const string LocalHeaderFontFamily = "Jua";
        private const string LocalBodyFontFamily = "Gamja Flower";
        private const string LocalHeaderFontFileName = "Jua.ttf";
        private const string LocalBodyFontFileName = "GamjaFlower.ttf";
        private const uint PrivateFontResource = 0x10;
        private const string DefaultCampBundlePath = @"C:\Games\Steam\steamapps\common\Monster Prom 2 - Monster Camp\MonsterCamp_Data\StreamingAssets\aa\StandaloneWindows\profilesfontsets_assets_all_79f49ff1b358585c59c1388d6a773d92.bundle";
        private const string DefaultPreviewPath = @"D:\Codex_Trans\Monster-Prom-3-KR\build\preview\english_metatexts.txt";
        private const string FallbackFontName = "Malgun Gothic";

        private static readonly string[] HeaderNameHints =
        {
            "header", "title", "heading", "headline", "banner", "logo", "sectiontitle"
        };

        private static RoadtripKoreanFontBridgePlugin _instance;

        private ConfigEntry<bool> _enableFontBridge;
        private ConfigEntry<bool> _enableMetatextOverride;
        private ConfigEntry<string> _roadtripBundlePath;
        private ConfigEntry<string> _localFontDirectory;
        private ConfigEntry<string> _bundlePath;
        private ConfigEntry<string> _previewPath;
        private ConfigEntry<string> _headerFontName;
        private ConfigEntry<string> _bodyFontName;
        private ConfigEntry<int> _headerSizeThreshold;

        private Harmony _harmony;
        private readonly List<AssetBundle> _fontBundles = new List<AssetBundle>();
        private readonly List<string> _registeredPrivateFontPaths = new List<string>();
        private readonly List<Font> _dynamicFonts = new List<Font>();
        private Font _headerFont;
        private Font _bodyFont;
        private Font _fallbackFont;
        private bool _fallbackCoverageChecked;
        private bool _fallbackHasCoverage;
        private bool _missingPreviewLogged;
        private TextAsset _previewTextAsset;
        private readonly HashSet<string> _loggedApplyErrors = new HashSet<string>(StringComparer.Ordinal);

        private static RoadtripKoreanFontBridgePlugin Instance
        {
            get { return _instance; }
        }

        private void Awake()
        {
            _instance = this;
            _enableFontBridge = Config.Bind("Fonts", "EnableFontBridge", true,
                "Load the optional Korean fonts and apply them to NGUI/UI text components.");
            _enableMetatextOverride = Config.Bind("Metatexts", "EnablePreviewOverride", true,
                "Replace english_metatexts with the local build/preview file when it exists.");
            _roadtripBundlePath = Config.Bind("Fonts", "RoadtripFontBundlePath", DefaultRoadtripBundlePath,
                "Path to the optional Unity 2021-compatible Jua/GamjaFlower bundle built for Monster Roadtrip.");
            _localFontDirectory = Config.Bind("Fonts", "LocalFontDirectory", DefaultLocalFontDirectory,
                "Directory containing local Jua.ttf and GamjaFlower.ttf. Fonts are registered privately for this process only.");
            _bundlePath = Config.Bind("Fonts", "MonsterCampFontBundlePath", DefaultCampBundlePath,
                "Fallback source path to Monster Camp's original Unity 2019 profilesfontsets bundle. Cross-version loading is unverified.");
            _previewPath = Config.Bind("Metatexts", "PreviewFilePath", DefaultPreviewPath,
                "Path to this project's ignored build/preview/english_metatexts.txt file.");
            _headerFontName = Config.Bind("Fonts", "HeaderFontAssetName", "Jua",
                "Exact Font asset name expected from the Monster Camp bundle.");
            _bodyFontName = Config.Bind("Fonts", "BodyFontAssetName", "GamjaFlower",
                "Exact Font asset name expected from the Monster Camp bundle.");
            _headerSizeThreshold = Config.Bind("Fonts", "HeaderFontSizeThreshold", 32,
                "Text at or above this font size uses Jua; names containing title/header hints also use Jua.");

            if (_enableFontBridge.Value)
            {
                LoadFonts();
                SceneManager.sceneLoaded += OnSceneLoaded;
            }

            _harmony = new Harmony(PluginGuid);
            PatchConfiguredMethods();

            if (_enableFontBridge.Value)
            {
                ApplyFontsToExistingComponents();
            }

            Logger.LogInfo("Initialized. Runtime game output and Unity 2019 bundle compatibility have not been tested.");
        }

        private void OnDestroy()
        {
            SceneManager.sceneLoaded -= OnSceneLoaded;
            if (_harmony != null)
            {
                _harmony.UnpatchSelf();
                _harmony = null;
            }

            if (_instance == this)
            {
                _instance = null;
            }

            ReleaseLocalFonts();
        }

        private void PatchConfiguredMethods()
        {
            if (_enableMetatextOverride.Value)
            {
                PatchMethod("BeautifulGlitch.CoreAssetManager", "GetTextAsset", new[] { typeof(string) }, "GetTextAssetPostfix");
            }

            if (!_enableFontBridge.Value)
            {
                return;
            }

            PatchMethod("UILabel", "OnEnable", Type.EmptyTypes, "ComponentOnEnablePostfix");
            PatchMethod("UnityEngine.UI.Text", "OnEnable", Type.EmptyTypes, "ComponentOnEnablePostfix");
            PatchMethod("BeautifulGlitch.LocalizedNGUIFont", "Refresh", Type.EmptyTypes, "LocalizedFontRefreshPostfix");
            PatchMethod("BeautifulGlitch.LocalizedTextFont", "Refresh", Type.EmptyTypes, "LocalizedFontRefreshPostfix");
        }

        private void PatchMethod(string typeName, string methodName, Type[] parameterTypes, string callbackName)
        {
            Type targetType = AccessTools.TypeByName(typeName);
            if (targetType == null)
            {
                Logger.LogWarning("Harmony target type not found: " + typeName + ". This patch was skipped.");
                return;
            }

            MethodBase target = AccessTools.Method(targetType, methodName, parameterTypes);
            if (target == null)
            {
                Logger.LogWarning("Harmony target method not found: " + typeName + "." + methodName + ". This patch was skipped.");
                return;
            }

            MethodInfo postfix = typeof(PatchCallbacks).GetMethod(callbackName, BindingFlags.Static | BindingFlags.NonPublic);
            if (postfix == null)
            {
                Logger.LogError("Internal Harmony callback not found: " + callbackName);
                return;
            }

            try
            {
                _harmony.Patch(target, postfix: new HarmonyMethod(postfix));
                Logger.LogInfo("Patched " + typeName + "." + methodName + ".");
            }
            catch (Exception ex)
            {
                Logger.LogError("Could not patch " + typeName + "." + methodName + ": " + ex);
            }
        }

        private void LoadFonts()
        {
            HashSet<char> requiredCharacters = CollectRequiredKoreanCharacters();
            // Prefer a bundle built with the game's Unity 2021 editor. Only use the
            // local process-private TTFs next, and the Unity 2019 Monster Camp bundle
            // only for roles still missing a valid font after that.
            TryLoadFontsFromBundle(_roadtripBundlePath.Value, "Roadtrip-compatible", requiredCharacters);
            if (_headerFont == null || _bodyFont == null)
            {
                TryLoadLocalFonts(requiredCharacters);
            }
            if (_headerFont == null || _bodyFont == null)
            {
                TryLoadFontsFromBundle(_bundlePath.Value, "Monster Camp Unity 2019", requiredCharacters);
            }

            if (_headerFont == null)
            {
                Logger.LogWarning("No validated header asset font was available; trying Windows " + FallbackFontName + ".");
                _headerFont = GetValidatedFallbackFont(requiredCharacters);
            }
            if (_bodyFont == null)
            {
                Logger.LogWarning("No validated body asset font was available; trying Windows " + FallbackFontName + ".");
                _bodyFont = GetValidatedFallbackFont(requiredCharacters);
            }

            Logger.LogInfo("Selected header font: " + FontDescription(_headerFont));
            Logger.LogInfo("Selected body font: " + FontDescription(_bodyFont));
        }

        private void TryLoadLocalFonts(HashSet<char> requiredCharacters)
        {
            string directory = string.IsNullOrWhiteSpace(_localFontDirectory.Value)
                ? string.Empty
                : _localFontDirectory.Value.Trim();
            if (directory.Length == 0 || !Directory.Exists(directory))
            {
                Logger.LogInfo("Local font directory not found; skipping private TTF fonts: " + directory);
                return;
            }

            string headerPath = Path.Combine(directory, LocalHeaderFontFileName);
            string bodyPath = Path.Combine(directory, LocalBodyFontFileName);
            bool headerRegistered = RegisterPrivateFont(headerPath, LocalHeaderFontFamily);
            bool bodyRegistered = RegisterPrivateFont(bodyPath, LocalBodyFontFamily);

            string[] installedFontNames = null;
            bool installedFontListAvailable = false;
            try
            {
                installedFontNames = Font.GetOSInstalledFontNames();
                installedFontListAvailable = installedFontNames != null;
                if (installedFontListAvailable)
                {
                    Logger.LogInfo("Unity reports " + installedFontNames.Length + " OS font family name(s) after private font registration.");
                }
            }
            catch (Exception ex)
            {
                Logger.LogWarning("Could not enumerate OS font names after private registration; dynamic font creation will be tested directly: " + ex.Message);
            }

            if (_headerFont == null)
            {
                Font candidate = TryCreateLocalDynamicFont(
                    LocalHeaderFontFamily, headerRegistered, installedFontNames, installedFontListAvailable,
                    requiredCharacters, "local Jua font");
                if (candidate != null)
                {
                    _headerFont = candidate;
                }
            }

            if (_bodyFont == null)
            {
                Font candidate = TryCreateLocalDynamicFont(
                    LocalBodyFontFamily, bodyRegistered, installedFontNames, installedFontListAvailable,
                    requiredCharacters, "local Gamja Flower font");
                if (candidate != null)
                {
                    _bodyFont = candidate;
                }
            }
        }

        private bool RegisterPrivateFont(string path, string familyName)
        {
            if (Environment.OSVersion.Platform != PlatformID.Win32NT)
            {
                Logger.LogWarning("Private font registration is only supported on Windows; skipping " + familyName + ".");
                return false;
            }

            if (string.IsNullOrWhiteSpace(path) || !File.Exists(path))
            {
                Logger.LogWarning("Local font file not found for " + familyName + ": " + path);
                return false;
            }

            string fullPath;
            try
            {
                fullPath = Path.GetFullPath(path);
            }
            catch (Exception ex)
            {
                Logger.LogWarning("Could not resolve local font path for " + familyName + ": " + ex.Message);
                return false;
            }

            try
            {
                int added = AddFontResourceExW(fullPath, PrivateFontResource, IntPtr.Zero);
                if (added <= 0)
                {
                    Logger.LogWarning("Windows did not register private font '" + familyName + "' from " + fullPath +
                        " (AddFontResourceExW returned " + added + ", Win32 error " + Marshal.GetLastWin32Error() + ").");
                    return false;
                }

                _registeredPrivateFontPaths.Add(fullPath);
                Logger.LogInfo("Registered private process-only font '" + familyName + "' from " + fullPath + ".");
                return true;
            }
            catch (Exception ex)
            {
                Logger.LogWarning("Private font registration failed for '" + familyName + "': " + ex.Message);
                return false;
            }
        }

        private Font TryCreateLocalDynamicFont(
            string familyName,
            bool privateFontRegistered,
            string[] installedFontNames,
            bool installedFontListAvailable,
            HashSet<char> requiredCharacters,
            string description)
        {
            if (!privateFontRegistered)
            {
                return null;
            }

            if (installedFontListAvailable && !ContainsFontFamily(installedFontNames, familyName))
            {
                Logger.LogWarning("Unity's OS font list does not contain privately registered family '" + familyName + "'. Falling back to the next font source.");
                return null;
            }

            Font candidate;
            try
            {
                candidate = Font.CreateDynamicFontFromOSFont(familyName, 32);
            }
            catch (Exception ex)
            {
                Logger.LogWarning("Unity could not create dynamic font '" + familyName + "' from the private registration: " + ex.Message);
                return null;
            }

            if (candidate == null)
            {
                Logger.LogWarning("Unity returned no dynamic Font for privately registered family '" + familyName + "'.");
                return null;
            }

            _dynamicFonts.Add(candidate);
            if (!HasKoreanGlyphCoverage(candidate, requiredCharacters, description + " ('" + familyName + "')"))
            {
                Logger.LogWarning("Privately registered font '" + familyName + "' failed Korean glyph coverage; falling back to the next font source.");
                return null;
            }

            Logger.LogInfo("Selected local dynamic font family '" + familyName + "'.");
            return candidate;
        }

        private static bool ContainsFontFamily(string[] fontNames, string familyName)
        {
            if (fontNames == null || string.IsNullOrWhiteSpace(familyName))
            {
                return false;
            }

            foreach (string fontName in fontNames)
            {
                if (string.Equals(fontName, familyName, StringComparison.OrdinalIgnoreCase))
                {
                    return true;
                }
            }

            return false;
        }

        private void ReleaseLocalFonts()
        {
            for (int i = _dynamicFonts.Count - 1; i >= 0; i--)
            {
                Font font = _dynamicFonts[i];
                if (font == null)
                {
                    continue;
                }

                try
                {
                    Destroy(font);
                }
                catch (Exception ex)
                {
                    Logger.LogWarning("Could not release dynamic font '" + font.name + "': " + ex.Message);
                }
            }
            _dynamicFonts.Clear();
            _headerFont = null;
            _bodyFont = null;
            _fallbackFont = null;

            for (int i = _registeredPrivateFontPaths.Count - 1; i >= 0; i--)
            {
                string path = _registeredPrivateFontPaths[i];
                try
                {
                    if (RemoveFontResourceExW(path, PrivateFontResource, IntPtr.Zero))
                    {
                        Logger.LogInfo("Removed private process-only font resource: " + path);
                    }
                    else
                    {
                        Logger.LogWarning("Windows did not remove private font resource '" + path + "' (Win32 error " + Marshal.GetLastWin32Error() + ").");
                    }
                }
                catch (Exception ex)
                {
                    Logger.LogWarning("Could not remove private font resource '" + path + "': " + ex.Message);
                }
            }
            _registeredPrivateFontPaths.Clear();
        }

        [DllImport("gdi32.dll", CharSet = CharSet.Unicode, EntryPoint = "AddFontResourceExW", SetLastError = true)]
        private static extern int AddFontResourceExW(string fileName, uint flags, IntPtr reserved);

        [DllImport("gdi32.dll", CharSet = CharSet.Unicode, EntryPoint = "RemoveFontResourceExW", SetLastError = true)]
        [return: MarshalAs(UnmanagedType.Bool)]
        private static extern bool RemoveFontResourceExW(string fileName, uint flags, IntPtr reserved);

        private void TryLoadFontsFromBundle(string path, string sourceDescription, HashSet<char> requiredCharacters)
        {
            if (string.IsNullOrWhiteSpace(path) || !File.Exists(path))
            {
                Logger.LogInfo(sourceDescription + " font bundle not found; skipping: " + path);
                return;
            }

            AssetBundle bundle;
            try
            {
                bundle = AssetBundle.LoadFromFile(path);
                if (bundle == null)
                {
                    Logger.LogWarning("AssetBundle.LoadFromFile returned null for " + sourceDescription + ": " + path);
                    return;
                }
                _fontBundles.Add(bundle);
            }
            catch (Exception ex)
            {
                Logger.LogWarning("Could not load " + sourceDescription + " font bundle: " + ex.Message);
                return;
            }

            Font[] loadedFonts = Array.Empty<Font>();
            try
            {
                loadedFonts = bundle.LoadAllAssets<Font>() ?? Array.Empty<Font>();
            }
            catch (Exception ex)
            {
                Logger.LogWarning(sourceDescription + " LoadAllAssets<Font>() failed: " + ex.Message);
            }
            Logger.LogInfo(sourceDescription + " bundle loaded; LoadAllAssets<Font>() returned " + loadedFonts.Length + " Font asset(s).");

            if (_headerFont == null)
            {
                Font candidate = FindFont(loadedFonts, _headerFontName.Value);
                if (candidate == null)
                {
                    candidate = TryLoadFontByName(bundle, _headerFontName.Value, sourceDescription);
                }
                if (candidate != null && HasKoreanGlyphCoverage(candidate, requiredCharacters, sourceDescription + " header font '" + candidate.name + "'"))
                {
                    _headerFont = candidate;
                }
                else if (candidate == null)
                {
                    Logger.LogWarning(sourceDescription + " bundle did not expose Font asset '" + _headerFontName.Value + "'.");
                }
            }

            if (_bodyFont == null)
            {
                Font candidate = FindFont(loadedFonts, _bodyFontName.Value);
                if (candidate == null)
                {
                    candidate = TryLoadFontByName(bundle, _bodyFontName.Value, sourceDescription);
                }
                if (candidate != null && HasKoreanGlyphCoverage(candidate, requiredCharacters, sourceDescription + " body font '" + candidate.name + "'"))
                {
                    _bodyFont = candidate;
                }
                else if (candidate == null)
                {
                    Logger.LogWarning(sourceDescription + " bundle did not expose Font asset '" + _bodyFontName.Value + "'.");
                }
            }
        }

        private Font TryLoadFontByName(AssetBundle bundle, string assetName, string sourceDescription)
        {
            if (bundle == null || string.IsNullOrWhiteSpace(assetName))
            {
                return null;
            }

            try
            {
                Font font = bundle.LoadAsset<Font>(assetName);
                if (font != null)
                {
                    Logger.LogInfo(sourceDescription + " direct lookup found Font asset '" + font.name + "'.");
                    if (!string.Equals(font.name, assetName, StringComparison.OrdinalIgnoreCase))
                    {
                        Logger.LogWarning("Requested Font asset '" + assetName + "' but direct lookup returned '" + font.name + "'.");
                        return null;
                    }
                }
                return font;
            }
            catch (Exception ex)
            {
                Logger.LogWarning(sourceDescription + " LoadAsset<Font>(\"" + assetName + "\") failed: " + ex.Message);
                return null;
            }
        }

        private static Font FindFont(IEnumerable<Font> fonts, string assetName)
        {
            if (fonts == null || string.IsNullOrWhiteSpace(assetName))
            {
                return null;
            }

            foreach (Font font in fonts)
            {
                if (font != null && string.Equals(font.name, assetName, StringComparison.OrdinalIgnoreCase))
                {
                    return font;
                }
            }

            return null;
        }

        private Font GetValidatedFallbackFont(HashSet<char> requiredCharacters)
        {
            if (_fallbackFont == null)
            {
                try
                {
                    _fallbackFont = Font.CreateDynamicFontFromOSFont(FallbackFontName, 32);
                    if (_fallbackFont != null)
                    {
                        _dynamicFonts.Add(_fallbackFont);
                    }
                }
                catch (Exception ex)
                {
                    Logger.LogError("Could not create the Windows fallback font '" + FallbackFontName + "': " + ex.Message);
                    return null;
                }
            }

            if (_fallbackFont == null)
            {
                Logger.LogError("Unity could not create the Windows fallback font '" + FallbackFontName + "'.");
                return null;
            }

            if (!_fallbackCoverageChecked)
            {
                _fallbackCoverageChecked = true;
                _fallbackHasCoverage = HasKoreanGlyphCoverage(_fallbackFont, requiredCharacters, "fallback font '" + FallbackFontName + "'");
            }

            if (!_fallbackHasCoverage)
            {
                Logger.LogError("The fallback font does not cover all Korean characters found in the local translation output. A font was left unset for roles that have no valid asset font.");
                return null;
            }

            return _fallbackFont;
        }

        private bool HasKoreanGlyphCoverage(Font font, HashSet<char> requiredCharacters, string description)
        {
            if (font == null)
            {
                return false;
            }

            char[] chars = requiredCharacters == null ? Array.Empty<char>() : requiredCharacters.ToArray();
            try
            {
                if (chars.Length > 0)
                {
                    font.RequestCharactersInTexture(new string(chars), 32, FontStyle.Normal);
                }
            }
            catch (Exception ex)
            {
                Logger.LogDebug("RequestCharactersInTexture for " + description + " returned: " + ex.Message);
            }

            List<char> missing = new List<char>();
            try
            {
                foreach (char character in chars)
                {
                    if (!font.HasCharacter(character))
                    {
                        missing.Add(character);
                    }
                }
            }
            catch (Exception ex)
            {
                Logger.LogWarning("Could not inspect glyph coverage for " + description + ": " + ex.Message);
                return false;
            }

            if (missing.Count > 0)
            {
                string examples = new string(missing.Take(12).ToArray());
                Logger.LogWarning(description + " is missing " + missing.Count + " of " + chars.Length + " required Korean character(s); examples: " + examples);
                return false;
            }

            Logger.LogInfo(description + " passed the Korean glyph check (" + chars.Length + " distinct required character(s)).");
            return true;
        }

        private HashSet<char> CollectRequiredKoreanCharacters()
        {
            HashSet<char> result = new HashSet<char>();
            AddKoreanCharactersFromFile(_previewPath.Value, result);

            try
            {
                string previewDirectory = Path.GetDirectoryName(Path.GetFullPath(_previewPath.Value));
                DirectoryInfo buildDirectory = string.IsNullOrEmpty(previewDirectory) ? null : Directory.GetParent(previewDirectory);
                DirectoryInfo projectRoot = buildDirectory == null ? null : buildDirectory.Parent;
                if (projectRoot != null)
                {
                    string eventOutputDirectory = Path.Combine(projectRoot.FullName, "build", "playtest", "game_assets", "texts");
                    if (Directory.Exists(eventOutputDirectory))
                    {
                        foreach (string file in Directory.GetFiles(eventOutputDirectory, "english_events_*.txt"))
                        {
                            AddKoreanCharactersFromFile(file, result);
                        }
                    }
                }
            }
            catch (Exception ex)
            {
                Logger.LogWarning("Could not locate all local event outputs for glyph checking: " + ex.Message);
            }

            if (result.Count == 0)
            {
                foreach (char character in "한국어가나다라마바사아자차카타파하번역설정메뉴")
                {
                    result.Add(character);
                }
                Logger.LogWarning("No local Korean preview/event output was found; glyph checking uses a short Korean probe only.");
            }

            Logger.LogInfo("Glyph check input contains " + result.Count + " distinct Korean character(s).");
            return result;
        }

        private static void AddKoreanCharactersFromFile(string path, HashSet<char> destination)
        {
            if (destination == null || string.IsNullOrWhiteSpace(path) || !File.Exists(path))
            {
                return;
            }

            try
            {
                string content = File.ReadAllText(path);
                foreach (char character in content)
                {
                    if (IsKoreanCharacter(character))
                    {
                        destination.Add(character);
                    }
                }
            }
            catch
            {
                // The font bridge can still start using the sample probe if local files are unreadable.
            }
        }

        private static bool IsKoreanCharacter(char character)
        {
            return (character >= '\uAC00' && character <= '\uD7A3') ||
                   (character >= '\u1100' && character <= '\u11FF') ||
                   (character >= '\u3130' && character <= '\u318F') ||
                   (character >= '\uA960' && character <= '\uA97F') ||
                   (character >= '\uD7B0' && character <= '\uD7FF');
        }

        private void ApplyFontsToExistingComponents()
        {
            int visited = 0;
            Type labelType = AccessTools.TypeByName("UILabel");
            if (labelType != null)
            {
                foreach (UnityEngine.Object found in Resources.FindObjectsOfTypeAll(labelType))
                {
                    Component component = found as Component;
                    if (component != null && component.gameObject != null && component.gameObject.scene.IsValid())
                    {
                        ApplyFontToTarget(component, false);
                        visited++;
                    }
                }
            }

            foreach (Text text in Resources.FindObjectsOfTypeAll<Text>())
            {
                if (text != null && text.gameObject != null && text.gameObject.scene.IsValid())
                {
                    ApplyFontToTarget(text, false);
                    visited++;
                }
            }

            Logger.LogDebug("Initial font pass inspected " + visited + " existing UI text component(s).");
        }

        private void OnSceneLoaded(Scene scene, LoadSceneMode mode)
        {
            ApplyFontsToExistingComponents();
        }

        private void ApplyLocalizedFont(object localizedComponent)
        {
            if (localizedComponent == null)
            {
                return;
            }

            FieldInfo labelField = AccessTools.Field(localizedComponent.GetType(), "label");
            if (labelField == null)
            {
                Logger.LogWarning("Could not find the 'label' field on " + localizedComponent.GetType().FullName + ".");
                return;
            }

            object label = labelField.GetValue(localizedComponent);
            if (label != null)
            {
                ApplyFontToTarget(label, true);
            }
        }

        private void ApplyFontToTarget(object target, bool force)
        {
            Component component = target as Component;
            if (component == null || component.gameObject == null)
            {
                return;
            }

            Font selectedFont = IsHeader(component) ? _headerFont : _bodyFont;
            if (selectedFont == null)
            {
                selectedFont = _bodyFont ?? _headerFont;
            }
            if (selectedFont == null)
            {
                return;
            }

            try
            {
                Text uiText = target as Text;
                if (uiText != null)
                {
                    bool hasLocalizer = HasComponent(component, "BeautifulGlitch.LocalizedTextFont");
                    if (!force && uiText.font == null && !hasLocalizer)
                    {
                        return;
                    }

                    if (uiText.font != selectedFont)
                    {
                        uiText.font = selectedFont;
                    }
                    return;
                }

                if (string.Equals(target.GetType().Name, "UILabel", StringComparison.Ordinal))
                {
                    PropertyInfo trueTypeFont = AccessTools.Property(target.GetType(), "trueTypeFont");
                    Font currentFont = trueTypeFont == null ? null : trueTypeFont.GetValue(target, null) as Font;
                    bool hasLocalizer = HasComponent(component, "BeautifulGlitch.LocalizedNGUIFont");
                    if (!force && currentFont == null && !hasLocalizer)
                    {
                        // Preserve bitmap-only labels, which may be used for icons or symbols.
                        return;
                    }

                    if (trueTypeFont != null && trueTypeFont.CanWrite)
                    {
                        if (currentFont != selectedFont)
                        {
                            trueTypeFont.SetValue(target, selectedFont, null);
                        }
                        return;
                    }

                    MethodInfo setter = AccessTools.Method(target.GetType(), "SetTrueTypeFont", new[] { typeof(Font) });
                    if (setter != null)
                    {
                        setter.Invoke(target, new object[] { selectedFont });
                    }
                }
            }
            catch (Exception ex)
            {
                string typeName = target.GetType().FullName;
                if (_loggedApplyErrors.Add(typeName))
                {
                    Logger.LogWarning("Could not apply a Korean font to " + typeName + ": " + ex.Message);
                }
            }
        }

        private bool IsHeader(Component component)
        {
            string objectName = component.gameObject == null ? string.Empty : component.gameObject.name;
            string componentName = component.name ?? string.Empty;
            string combined = (objectName + " " + componentName).ToLowerInvariant();
            foreach (string hint in HeaderNameHints)
            {
                if (combined.Contains(hint))
                {
                    return true;
                }
            }

            PropertyInfo sizeProperty = AccessTools.Property(component.GetType(), "fontSize");
            if (sizeProperty != null)
            {
                try
                {
                    object value = sizeProperty.GetValue(component, null);
                    if (value != null && Convert.ToInt32(value) >= _headerSizeThreshold.Value)
                    {
                        return true;
                    }
                }
                catch
                {
                    // Fall back to the body font when the component's size cannot be read.
                }
            }

            return false;
        }

        private static bool HasComponent(Component component, string typeName)
        {
            Type componentType = AccessTools.TypeByName(typeName);
            return component != null && componentType != null && component.GetComponent(componentType) != null;
        }

        private TextAsset LoadPreviewOverride()
        {
            if (_previewTextAsset != null)
            {
                return _previewTextAsset;
            }

            string path = _previewPath.Value == null ? string.Empty : _previewPath.Value.Trim();
            if (path.Length == 0 || !File.Exists(path))
            {
                if (!_missingPreviewLogged)
                {
                    Logger.LogWarning("Local metatext preview was not found; the game's original english_metatexts asset will be used. Path: " + path);
                    _missingPreviewLogged = true;
                }
                return null;
            }

            try
            {
                string contents = File.ReadAllText(path);
                TextAsset replacement = new TextAsset(contents);
                replacement.name = "english_metatexts";
                _previewTextAsset = replacement;
                Logger.LogInfo("Loaded local english_metatexts preview (" + contents.Length + " characters) from " + path);
                return _previewTextAsset;
            }
            catch (Exception ex)
            {
                Logger.LogError("Could not read the local metatext preview; the original asset will be kept: " + ex.Message);
                return null;
            }
        }

        private static string FontDescription(Font font)
        {
            return font == null ? "<unavailable>" : "'" + font.name + "'";
        }

        private static class PatchCallbacks
        {
            private static void GetTextAssetPostfix(string __0, ref TextAsset __result)
            {
                RoadtripKoreanFontBridgePlugin plugin = Instance;
                if (plugin == null || !plugin._enableMetatextOverride.Value ||
                    !string.Equals(__0, "english_metatexts", StringComparison.Ordinal))
                {
                    return;
                }

                TextAsset replacement = plugin.LoadPreviewOverride();
                if (replacement != null)
                {
                    __result = replacement;
                }
            }

            private static void ComponentOnEnablePostfix(object __instance)
            {
                RoadtripKoreanFontBridgePlugin plugin = Instance;
                if (plugin != null && plugin._enableFontBridge.Value)
                {
                    plugin.ApplyFontToTarget(__instance, false);
                }
            }

            private static void LocalizedFontRefreshPostfix(object __instance)
            {
                RoadtripKoreanFontBridgePlugin plugin = Instance;
                if (plugin != null && plugin._enableFontBridge.Value)
                {
                    plugin.ApplyLocalizedFont(__instance);
                }
            }
        }
    }
}
