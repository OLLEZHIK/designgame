using UnityEngine;

namespace BugWar.UI
{
    /// <summary>
    /// Палитра дизайн-системы BugWar v1.0 («Deep Teal &amp; Honey»).
    /// Источник правды — tokens/tokens.json в репозитории дизайн-системы; при изменении обновлять оба файла.
    /// </summary>
    public static class BugWarPalette
    {
        // Фон
        public static readonly Color BackgroundBase = Hex(0x004A56);
        public static readonly Color BackgroundPattern = Hex(0x0A5A66);
        public static readonly Color BackgroundGlow = Hex(0xFFD36A);

        // Поверхности
        public static readonly Color Panel = Hex(0x003A44);
        public static readonly Color PanelEdge = Hex(0x0F5A66);
        public static readonly Color PanelLip = Hex(0x00191E);
        public static readonly Color Well = Hex(0x00252C);
        public static readonly Color Button = Hex(0x005564);
        public static readonly Color ButtonLip = Hex(0x00303A);

        // Главное действие (мёд)
        public static readonly Color PrimaryTop = Hex(0xFFC51B);
        public static readonly Color PrimaryBottom = Hex(0xFF8C00);
        public static readonly Color PrimaryLip = Hex(0xB14B00);
        public static readonly Color PrimarySpark = Hex(0xFFF3C4);

        // Акценты
        public static readonly Color Mint = Hex(0x4CF0C0);
        public static readonly Color MintDark = Hex(0x22B88E);
        public static readonly Color Gold = Hex(0xFFD23F);

        // Статусы
        public static readonly Color Badge = Hex(0xF42C2C);
        public static readonly Color Plus = Hex(0x30D030);
        public static readonly Color Locked = Hex(0x6E8A8E);

        // Текст
        public static readonly Color TextPrimary = Hex(0xFFFFFF);
        public static readonly Color TextSecondary = Hex(0xD2E2E0);
        public static readonly Color TextMuted = Hex(0x9DBDBD);
        public static readonly Color TextCream = Hex(0xF6F0DE);
        public static readonly Color TextOutline = Hex(0x08242C);
        public static readonly Color TextShadow = Hex(0x051A20);

        private static Color Hex(int rgb) =>
            new Color(((rgb >> 16) & 0xFF) / 255f, ((rgb >> 8) & 0xFF) / 255f, (rgb & 0xFF) / 255f, 1f);
    }
}
