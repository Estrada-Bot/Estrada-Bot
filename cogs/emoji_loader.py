"""
نظام تحميل Application Emojis أوتوماتيك.
كل الإيموجي كيتقراو نيشان من Discord Portal (bot.fetch_application_emojis())
بنفس الاسم الحقيقي اللي مرفوعين بيه (نفس اسم الملف فـ bot_emojis/، مثلاً
fl_locked, fl_check...) — بلا أي جدول ترجمة وسيط.
"""
import discord
from discord.ext import commands
import sys

# أسماء الإيموجي المتوقعة (لغرض التقرير فـ on_ready فقط — اختياري تماماً).
EMOJI_NAMES = [
    "60226check", "8118xmark", "11838warning", "78934verified", "7490modernverify",
    "80091fermer", "9068ouvert", "747328ownericon", "300018dmids", "476439dmids",
    "29909ticket", "82382member", "80271admin", "52657staff", "11757home",
    "32535applicationapprivedids", "9275yellowstar", "41378statistiques",
    "15830voicechannelgreenalt", "90665shoppingcart", "6619megaphone", "95805bot",
    "36438designer", "26295bolt", "64005web", "62470logs", "8997modernrefresh",
    "14385supprimer", "50494lien", "85722ajouter", "19492membres",
    "834134giftingchampion",
]

# ── الـ cache — يُملأ عند on_ready، مفتاحو هو الاسم الحقيقي فـ Discord ──────
_emoji_cache: dict[str, discord.Emoji] = {}


def get(name: str) -> str:
    """
    ارجع الإيموجي كنص جاهز (مثل: <:fl_check:123456>) بالاسم الحقيقي ديالو
    فـ Discord Portal. إذا ما وُجدش يرجع نص فارغ بدل ما يكرّش.
    """
    emoji = _emoji_cache.get(name)
    return str(emoji) if emoji else ""


def get_obj(name: str):
    """ارجع كائن discord.Emoji مباشرة (للاستخدام في emoji= داخل Button)."""
    return _emoji_cache.get(name)


async def load_emojis(bot: commands.Bot):
    """احمّل كل Application Emojis من Discord API نيشان، بلا أي ترجمة.
    ملاحظة مهمة: on_ready يمكن يتعاود منين البوت يدير reconnect لـ Discord
    (هادشي عادي وكيوقع بزاف). إلا فشل التحميل فـ إحدى هاد المرات (مثلاً
    rate limit مؤقت)، كنخليو الكاش القديمة الصحيحة كيفما هي بدل ما نمسحوها
    — أحسن نبقاو بإيموجي قديمة شوية من ما نبقاو بلا إيموجي خالص."""
    global _emoji_cache
    try:
        app_emojis = await bot.fetch_application_emojis()
        _emoji_cache = {e.name: e for e in app_emojis}

        loaded  = [n for n in EMOJI_NAMES if n in _emoji_cache]
        missing = [n for n in EMOJI_NAMES if n not in _emoji_cache]

        print(f"✅ Application Emojis: {len(loaded)}/{len(EMOJI_NAMES)} محمّلة")
        if missing:
            print(f"⚠️  ناقص في Dev Portal: {', '.join(missing)}")
        print(f"🔎 [debug] كل الأسماء الحقيقية المحمّلة فعلياً ({len(_emoji_cache)}): {sorted(_emoji_cache.keys())}")
    except Exception as e:
        # كنخليو _emoji_cache بحالها (ماشي {}) — تبقى آخر نسخة صحيحة معروفة.
        print(f"⚠️  فشل تحميل Application Emojis (باقي نستعملو آخر كاش صحيحة، {len(_emoji_cache)} إيموجي): {e}")


class TextEmojiMap(dict):
    """
    قاموس خاص لاستعمال EMOJI["key"] كيفما هو مستعمل فـ الكود القديم، لكن
    كل قيمة كتخزن كـ (real_name, unicode_fallback) — ومنين تقرا EMOJI["key"]،
    كيرجع ليك الإيموجي الحقيقي ديالك (إلا كان محمّل) وإلا اليونيكود
    كاحتياط فقط. بلا ما تحتاج تبدل شي حاجة أخرى فـ الكود.
    """
    def __getitem__(self, key):
        real_name, fallback = super().__getitem__(key)
        if real_name is None:
            return fallback
        return get(real_name) or fallback


class EmojiLoader(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        await load_emojis(self.bot)


async def setup(bot):
    await bot.add_cog(EmojiLoader(bot))
