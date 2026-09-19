"""Idempotent seed data for local/dev Postgres.

Safe to re-run: each complaint's id is derived deterministically from its
text via uuid5(NAMESPACE_DNS, text), and inserts use ON CONFLICT (id) DO
NOTHING, so re-running never duplicates rows.
"""

import sys
from pathlib import Path
from uuid import NAMESPACE_DNS, uuid5

from sqlalchemy.orm import Session

if __name__ == "__main__" and __package__ is None:
    # Allow `python scripts/seed.py` in addition to `python -m scripts.seed`
    # by putting the backend/ dir (parent of this file's directory) on sys.path.
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.db import SessionLocal
from app.domain.enums import Category, Priority
from app.repositories.complaints import ComplaintRepository, NewComplaint

COMPLAINTS: list[dict] = [
    dict(
        text="Water pipeline burst near Gulshan Chowk since early morning, sara area mein paani hi paani ho gaya hai, road completely flooded, please send repair team on urgent basis.",
        location="Gulshan-e-Iqbal, Block 5, Karachi",
        category=Category.WATER,
        priority=Priority.HIGH,
        reporter_contact="0300-1234567",
        ai_summary="Burst water pipeline flooding Gulshan Chowk road",
        triaged_by="llm:groq",
        triage_latency_ms=380,
    ),
    dict(
        text="No water supply in our mohalla from last 4 days, tanker bhi nahi aaya, elderly and children suffering badly, kindly resolve on urgent basis.",
        location="Gali 12, Dhoke Kashmirian, Rawalpindi",
        category=Category.WATER,
        priority=Priority.HIGH,
        ai_summary="4-day water outage, no tanker supply",
        triaged_by="llm:groq",
        triage_latency_ms=410,
    ),
    dict(
        text="Water pressure bohot low hai in our street pichle hafte se, upper floor walon ko paani nahi mil raha theek se.",
        location="Johar Town Phase 2, Lahore",
        category=Category.WATER,
        priority=Priority.NORMAL,
        reporter_contact="sana.malik@example.com",
        ai_summary="Low water pressure affecting upper floors",
        triaged_by="rules",
        triage_latency_ms=12,
    ),
    dict(
        text="Sewerage water thora sa leak ho raha hai from the main line, abhi zyada issue nahi hai but should be checked before it worsens.",
        location="PECHS Block 6, Karachi",
        category=Category.WATER,
        priority=Priority.LOW,
        ai_summary="Minor sewerage leak from main line",
        triaged_by="llm:ollama",
        triage_latency_ms=610,
    ),
    dict(
        text="Underground water pipe burst kal raat se, whole street submerged, cars cannot pass, is a safety hazard for bikes at night.",
        location="Satellite Town, Rawalpindi",
        category=Category.WATER,
        priority=Priority.HIGH,
        ai_summary="Underground pipe burst submerging street",
        triaged_by="llm:groq",
        triage_latency_ms=355,
    ),
    dict(
        text="Naya connection apply kiya tha do mahine pehle lekin abhi tak water board ne install nahi kiya, follow up chahiye.",
        location="Latifabad Unit 7, Hyderabad",
        category=Category.WATER,
        priority=Priority.NORMAL,
        ai_summary="Pending water connection installation for two months",
        triaged_by="rules",
        triage_latency_ms=16,
    ),
    dict(
        text="Transformer sparking badly near house number 45, bacho ka khel na wahan bohot khatarnak hai, please send WAPDA team immediately.",
        location="Al-Rehman Colony, Multan",
        category=Category.ELECTRICITY,
        priority=Priority.HIGH,
        reporter_contact="0321-9876543",
        ai_summary="Sparking transformer poses danger to children",
        triaged_by="llm:groq",
        triage_latency_ms=290,
    ),
    dict(
        text="Bijli ki taar looz ho kar sadak par latak rahi hai after yesterday's storm, bahut khatarnak situation hai for pedestrians.",
        location="Shadman Colony, Lahore",
        category=Category.ELECTRICITY,
        priority=Priority.HIGH,
        ai_summary="Loose live wire hanging over road after storm",
        triaged_by="llm:groq",
        triage_latency_ms=330,
    ),
    dict(
        text="Frequent bijli ki band-o-band hamare area mein pichle hafte se, transformer purana lag raha hai, needs inspection.",
        location="North Nazimabad Block H, Karachi",
        category=Category.ELECTRICITY,
        priority=Priority.NORMAL,
        ai_summary="Frequent power outages, transformer needs inspection",
        triaged_by="rules",
        triage_latency_ms=15,
    ),
    dict(
        text="Street ka ek electricity pole thora jhuk gaya hai, filhal koi khatra nahi lekin dekh lein please.",
        location="Gulberg III, Lahore",
        category=Category.ELECTRICITY,
        priority=Priority.LOW,
        ai_summary="Electricity pole leaning slightly, no immediate danger",
        triaged_by="rules:fallback",
        triage_latency_ms=8,
    ),
    dict(
        text="Open electric wire near the park entrance is sparking every time it rains, bachay park mein khelte hain, very dangerous.",
        location="F-10 Markaz, Islamabad",
        category=Category.ELECTRICITY,
        priority=Priority.HIGH,
        reporter_contact="0333-4567890",
        ai_summary="Sparking open wire near park entrance, danger to children",
        triaged_by="llm:ollama",
        triage_latency_ms=540,
    ),
    dict(
        text="Meter reading galat aa rahi hai last do bills se, bill bohot zyada aa raha hai actual usage se, please check karwayein.",
        location="Wapda Town, Lahore",
        category=Category.ELECTRICITY,
        priority=Priority.NORMAL,
        ai_summary="Incorrect meter readings causing inflated bills",
        triaged_by="llm:groq",
        triage_latency_ms=320,
    ),
    dict(
        text="Garbage not collected from our street for over a week now, bohot badbu phael rahi hai, kachra truck nahi aaya.",
        location="Liaquatabad Block 2, Karachi",
        category=Category.SANITATION,
        priority=Priority.NORMAL,
        ai_summary="Garbage uncollected for a week, causing odor",
        triaged_by="llm:groq",
        triage_latency_ms=300,
    ),
    dict(
        text="Sewerage overflow ho raha hai humare gali mein last 3 din se, ganda pani ghar ke andar aa raha hai, please emergency response chahiye.",
        location="Chah Miran, Lahore",
        category=Category.SANITATION,
        priority=Priority.HIGH,
        reporter_contact="0345-1122334",
        ai_summary="Sewage overflow entering homes, urgent",
        triaged_by="llm:groq",
        triage_latency_ms=275,
    ),
    dict(
        text="Kachra kaafi jama ho gaya hai empty plot par, mosquito aur bimari phailne ka khadsha hai, please clean up karwayein.",
        location="Samanabad, Lahore",
        category=Category.SANITATION,
        priority=Priority.NORMAL,
        ai_summary="Garbage pile on empty plot, health hazard risk",
        triaged_by="rules",
        triage_latency_ms=20,
    ),
    dict(
        text="Community dustbin thora purana ho gaya hai aur lid tooti hui hai, replace kar dein jab convenient ho.",
        location="DHA Phase 6, Karachi",
        category=Category.SANITATION,
        priority=Priority.LOW,
        ai_summary="Community dustbin lid broken, needs replacement",
        triaged_by="rules:fallback",
        triage_latency_ms=6,
    ),
    dict(
        text="Nala overflow ho kar sadak par ganda pani aa raha hai teen din se, bachon ka school jana mushkil ho gaya hai.",
        location="Ichhra, Lahore",
        category=Category.SANITATION,
        priority=Priority.HIGH,
        ai_summary="Overflowing drain flooding road with sewage",
        triaged_by="llm:groq",
        triage_latency_ms=360,
    ),
    dict(
        text="Dead animal (bakri) sadak kinare pare hue teen din ho gaye hain, bohot badbu aur bimari failne ka khatra hai mohalle mein.",
        location="Nazimabad No. 3, Karachi",
        category=Category.SANITATION,
        priority=Priority.HIGH,
        ai_summary="Dead animal on roadside for three days, health hazard",
        triaged_by="llm:groq",
        triage_latency_ms=265,
    ),
    dict(
        text="Bahut bara pothole ban gaya hai main road par, kal do motorcycle iski wajah se gir gaye, urgent repair chahiye is se pehle koi bara accident ho.",
        location="Ferozepur Road, Lahore",
        category=Category.ROADS,
        priority=Priority.HIGH,
        reporter_contact="0301-2345678",
        ai_summary="Large pothole causing motorcycle accidents",
        triaged_by="llm:groq",
        triage_latency_ms=310,
    ),
    dict(
        text="Road surface kaafi uneven ho gayi hai hamare block mein, driving mein dikkat hoti hai especially raat ko.",
        location="Gulshan-e-Ravi, Lahore",
        category=Category.ROADS,
        priority=Priority.NORMAL,
        ai_summary="Uneven road surface causing driving difficulty",
        triaged_by="rules",
        triage_latency_ms=14,
    ),
    dict(
        text="Sadak dhans gayi hai heavy rain ke baad, bara gaddha ban gaya hai jo raat mein nazar nahi aata, bohot khatarnak hai.",
        location="Airport Road, Peshawar",
        category=Category.ROADS,
        priority=Priority.HIGH,
        ai_summary="Road collapse after rain creates hazardous crater",
        triaged_by="llm:ollama",
        triage_latency_ms=590,
    ),
    dict(
        text="Speed breaker thora sa high ban gaya hai naye construction ke baad, cars scrape ho rahi hain, please level kar dein.",
        location="Bahria Town Phase 4, Rawalpindi",
        category=Category.ROADS,
        priority=Priority.LOW,
        ai_summary="Speed breaker too high, scraping vehicles",
        triaged_by="rules:fallback",
        triage_latency_ms=9,
    ),
    dict(
        text="Bridge ki railing tooti hui hai for two weeks now, bachay uske paas se guzarte hain school jate waqt, please fix urgently.",
        location="Ravi Road, Lahore",
        category=Category.ROADS,
        priority=Priority.HIGH,
        ai_summary="Broken bridge railing near school route",
        triaged_by="llm:groq",
        triage_latency_ms=295,
    ),
    dict(
        text="Manhole cover missing hai road ke beech mein last hafte se, raat ko koi gir sakta hai, please temporary barrier bhi laga dein.",
        location="Cavalry Ground, Lahore",
        category=Category.ROADS,
        priority=Priority.NORMAL,
        reporter_contact="0312-9988776",
        ai_summary="Missing manhole cover on road, fall risk",
        triaged_by="llm:ollama",
        triage_latency_ms=480,
    ),
    dict(
        text="Poori gali ki streetlights band hain last 10 din se, raat ko bohot andhera hota hai, women feel unsafe walking.",
        location="Gulistan-e-Jauhar Block 13, Karachi",
        category=Category.STREETLIGHTS,
        priority=Priority.NORMAL,
        ai_summary="Street lights out for 10 days, safety concern at night",
        triaged_by="llm:groq",
        triage_latency_ms=340,
    ),
    dict(
        text="Ek streetlight flicker kar rahi hai corner par, abhi kaam kar rahi hai but jald kharab ho sakti hai.",
        location="Cantt Area, Multan",
        category=Category.STREETLIGHTS,
        priority=Priority.LOW,
        ai_summary="Flickering streetlight may fail soon",
        triaged_by="rules:fallback",
        triage_latency_ms=7,
    ),
    dict(
        text="3 streetlights dead hain park ke bahar, shaam ke baad walk karna mushkil ho gaya hai residents ke liye.",
        location="Model Town Park, Lahore",
        category=Category.STREETLIGHTS,
        priority=Priority.NORMAL,
        ai_summary="Three dead streetlights outside park",
        triaged_by="rules",
        triage_latency_ms=18,
    ),
    dict(
        text="Poora block andhere mein hai kyun ke saari streetlights ek sath fail ho gayi hain, crime ka khatra barh gaya hai raat ko.",
        location="Orangi Town Sector 5, Karachi",
        category=Category.STREETLIGHTS,
        priority=Priority.HIGH,
        reporter_contact="0308-6677889",
        ai_summary="Entire block dark, streetlight failure raises crime risk",
        triaged_by="llm:groq",
        triage_latency_ms=400,
    ),
    dict(
        text="Park ka jhoola (swing) tuta hua hai last month se, bachay khel nahi sakte theek se, please repair karwayein.",
        location="Askari Park, Rawalpindi",
        category=Category.OTHER,
        priority=Priority.NORMAL,
        ai_summary="Broken park swing needs repair",
        triaged_by="rules",
        triage_latency_ms=11,
    ),
    dict(
        text="Public bench park mein toot gayi hai, koi emergency nahi but replace ho jaye to acha rahega.",
        location="Jinnah Garden, Faisalabad",
        category=Category.OTHER,
        priority=Priority.LOW,
        ai_summary="Broken public bench in park",
        triaged_by="rules:fallback",
        triage_latency_ms=5,
    ),
    dict(
        text="Stray dogs ka group bohot aggressive ho gaya hai humare area mein, kal ek bacha bite ho gaya, please urgent action lein.",
        location="Township, Lahore",
        category=Category.OTHER,
        priority=Priority.HIGH,
        reporter_contact="0334-5566778",
        ai_summary="Aggressive stray dogs bit a child, urgent action needed",
        triaged_by="llm:groq",
        triage_latency_ms=425,
    ),
    dict(
        text="Noise pollution bohot zyada hai wedding halls ki wajah se raat gaye tak loud music, neighbours so nahi paa rahe.",
        location="Garden Town, Lahore",
        category=Category.OTHER,
        priority=Priority.NORMAL,
        ai_summary="Excessive night-time noise from wedding halls",
        triaged_by="llm:ollama",
        triage_latency_ms=560,
    ),
]


def seed(session: Session) -> tuple[int, int]:
    """Insert all seed complaints. Returns (inserted, skipped)."""
    repo = ComplaintRepository(session)
    inserted = 0
    skipped = 0
    for item in COMPLAINTS:
        complaint_id = uuid5(NAMESPACE_DNS, item["text"])
        data = NewComplaint(
            text=item["text"],
            location=item["location"],
            category=item["category"],
            priority=item["priority"],
            triaged_by=item["triaged_by"],
            triage_latency_ms=item["triage_latency_ms"],
            reporter_contact=item.get("reporter_contact"),
            ai_summary=item.get("ai_summary"),
        )
        if repo.create_with_id(complaint_id, data):
            inserted += 1
        else:
            skipped += 1
    return inserted, skipped


def main() -> None:
    session = SessionLocal()
    try:
        inserted, skipped = seed(session)
    finally:
        session.close()
    print(f"Seed complete: {inserted} inserted, {skipped} skipped (already present)")


if __name__ == "__main__":
    main()
