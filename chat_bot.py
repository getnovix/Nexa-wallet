from fastapi import APIRouter, Depends
from pydantic import BaseModel
from config import *
from auth import *
from validators import *
from database import get_db
import random

router = APIRouter()


class Chat(BaseModel):
    chat: str


@router.post("/chat_bot")
def chat(chat: Chat, phone: str = Depends(get_current_user)):
    chat_text = chat.chat.lower().strip()

    with get_db() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                SELECT *
                FROM users
                WHERE phone = %s
                """,
                (phone,)
            )
            db_user = cursor.fetchone()
            if not db_user:
                return {
                    "ok": False,
                    "message": "المستخدم غير موجود."
                }
            name = db_user["name"]

            cursor.execute(
                """
                SELECT *
                FROM usdt_balances
                WHERE phone = %s
                """,
                (phone,)
            )
            db_balance = cursor.fetchone()
            if not db_balance:
                return {"ok": False, "message": "لا يوجد محفظة"}
            balance = db_balance["balance"]

    chat_hello = [
        f"مرحبًا {name} 🌹، كيف حالك اليوم؟ يسعدني مساعدتك في أي استفسار يتعلق بمحفظة Nexa.",
        f"أهلًا وسهلًا بك يا {name} 😊، أنا مساعد Nexa الذكي، أخبرني بما تحتاج وسأبذل جهدي لمساعدتك.",
        f"سعدت برؤيتك يا {name} 💙، أتمنى أن يكون يومك رائعًا. كيف يمكنني خدمتك اليوم؟",
        f"مرحبًا {name} 👋، أنا جاهز للإجابة عن أسئلتك المتعلقة بالرصيد أو التحويلات أو أي خدمة داخل Nexa.",
        f"حيّاك الله يا {name} 🌟، يسعدني وجودك هنا. ما الذي ترغب في معرفته أو إنجازه اليوم؟",
        f"أهلًا بك {name} 🤝، إذا احتجت أي مساعدة في استخدام Nexa فأنا هنا لمساعدتك خطوة بخطوة.",
        f"مرحبًا {name} ✨، أتمنى أن تكون بخير. اسألني أي سؤال يخص محفظتك أو خدمات Nexa.",
        f"سعيد بانضمامك يا {name} 💚، أخبرني بما تحتاج وسأساعدك بأفضل طريقة ممكنة.",
        f"أهلًا {name} 🚀، أنا مستعد لمساعدتك في كل ما يتعلق بمحفظة Nexa والتحويلات والإيداع والسحب.",
        f"مرحبًا {name} 😊، شكرًا لاستخدامك Nexa. كيف أستطيع مساعدتك اليوم؟"
    ]

    chat_balance_low = [
        f"مرحبًا {name} 👋، رصيدك الحالي هو {balance} جنيه سوداني. يبدو أنه منخفض، وإذا كنت ترغب في زيادة رصيدك فأنا جاهز لمساعدتك في خطوات الشحن.",
        f"أهلًا {name} 🌹، لاحظت أن رصيدك الحالي {balance} جنيه سوداني. إذا كنت تخطط لإجراء تحويل قريبًا فقد يكون من المناسب شحن المحفظة أولًا.",
        f"مرحبًا {name} 😊، لديك الآن {balance} جنيه سوداني فقط. إذا احتجت إلى شحن المحفظة أو معرفة الطرق المتاحة فأخبرني وسأرشدك.",
        f"أهلًا بك {name} ✨، رصيدك الحالي {balance} جنيه سوداني. أنصحك بإضافة رصيد حتى تتمكن من تنفيذ عملياتك بسهولة دون انقطاع.",
        f"مرحبًا {name} 💙، رصيدك الحالي {balance} جنيه سوداني. إذا كنت ترغب في إيداع مبلغ جديد أو تحتاج إلى شرح طريقة الشحن فأنا معك.",
        f"سعدت بوجودك يا {name} 🌟، أرى أن رصيدك الحالي {balance} جنيه سوداني، وهو أقل من الحد الذي قد تحتاجه لبعض العمليات. يسعدني مساعدتك في شحن المحفظة.",
        f"أهلًا {name} 🤝، رصيدك الحالي {balance} جنيه سوداني. إذا كنت تستعد لإرسال حوالة أو دفع خدمة، فقد تحتاج إلى زيادة الرصيد أولًا.",
        f"مرحبًا {name} 🚀، لديك {balance} جنيه سوداني في محفظتك. إذا أردت، يمكنني إرشادك إلى أسرع طريقة لإضافة رصيد.",
        f"أهلًا {name} 😊، رصيدك الحالي {balance} جنيه سوداني. لا تقلق، يمكننا شحن المحفظة خلال دقائق، فقط أخبرني بالطريقة التي تناسبك.",
        f"مرحبًا {name} 💚، رصيدك الحالي {balance} جنيه سوداني. أنا هنا لمساعدتك في أي استفسار حول الإيداع أو الشحن أو إدارة محفظتك."
    ]

    reply = []

    if (
        "السلام عليكم" in chat_text
        or "السلام" in chat_text
        or "hi" in chat_text
        or "هاي" in chat_text
        or "هلا" in chat_text
        or "اهلا" in chat_text
        or "هلو" in chat_text
    ):
        num = random.randint(0, 9)
        reply.append(chat_hello[num])

    if (
        "رصيدي" in chat_text
        or "كم رصيدي" in chat_text
        or "رصيدي كم" in chat_text
        or "الرصيد تبعي" in chat_text
        or "رصيدي اليوم" in chat_text
        or "فلوسي كم" in chat_text
        or "فلوسي" in chat_text
        or "اعرض الرصيد" in chat_text
        or "كم معي" in chat_text
        or "كم يوجد بمحفظتي" in chat_text
    ):
        if "من انت" in chat_text:
            reply.append("أنا مساعد Nexa الذكي، أساعدك في معرفة الرصيد، التحويلات، الإيداع، السحب، وإدارة حسابك.")
        if balance < 50000:
            num = random.randint(0, 9)
            reply.append(chat_balance_low[num])
        else:
            reply.append(
                f"مرحبًا {name} 🌹، رصيدك الحالي {balance} جنيه سوداني، ورصيدك جيد جدًا."
            )

    if not reply:
        reply.append("عذرًا، لم أفهم سؤالك. هل يمكنك إعادة صياغته؟")
    if "من انت" in chat_text:
        reply.append(f" يا استاذ {name} انا مجرد مساعد اساعدك في امور محفظتك فقط")
    if "كيفك" in chat_text:
        reply.append(" الحمد لله بخير شكرآ لسؤالك")
    return {
        "ok": True,
        "message": "\n\n".join(reply)
    }
