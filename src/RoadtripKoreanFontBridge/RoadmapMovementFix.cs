using System.Collections;

namespace RoadtripKoreanFontBridge
{
    public static class RoadmapMovementFix
    {
        // Harmony injects the first path argument and the private index field.
        // MultiLerp uses -1 as its finished-path sentinel. A fresh valid path
        // must start at section zero before UpdateMovement snapshots that field.
        public static void BeginPath(IList __0, ref int ___mCurrentPointIndex)
        {
            if (__0 != null && __0.Count >= 2)
            {
                ___mCurrentPointIndex = 0;
            }
        }
    }
}
