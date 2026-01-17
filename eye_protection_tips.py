"""
Eye Protection Tips for Study Owl Athena entity.

100 normal tips (simple, science-based) for normal Athena variant.
100 advanced tips (witty & insightful) for exceptional Athena variant.
"""

from typing import Tuple

# =============================================================================
# NORMAL TIPS - Simple, science-based eye protection tips
# =============================================================================

NORMAL_TIPS = [
    # 🌞 UV Protection (1-20)
    ("UV light can damage eyes over time. Long-term UV exposure is linked with higher risk of eye problems, so UV-blocking sunglasses are a genuine health measure.", "🌞"),
    ("Choose sunglasses that say '100% UV' or 'UV400.' This means they block UVA and UVB to a high degree; it is the label/standard that matters, not the darkness.", "🌞"),
    ("Dark lenses without UV protection can be worse than none. They can make your pupil open more while still letting UV in.", "🌞"),
    ("Different hazards need different protection. 'Eye protection' is not one thing: impact, chemical splash, and radiation hazards require different designs.", "🌞"),
    ("Regular glasses are not reliable safety gear. They are not tested the same way as safety eyewear and often leave gaps around the sides.", "🌞"),
    ("For flying debris or impact risk, use certified safety glasses. In many workplaces, certification is tied to standards such as ANSI/ISEA Z87.1.", "🌞"),
    ("For chemical splashes, goggles are usually better than 'safety glasses.' Goggles seal around the eye area and reduce splash entry.", "🌞"),
    ("For sprays/droplets (infection control), safety glasses are often not enough. Goggles offer better droplet/splash protection.", "🌞"),
    ("Vent design matters for splash protection. Directly-vented goggles can let splashes in; indirectly-vented or non-vented goggles are preferred.", "🌞"),
    ("Face shields protect more of the face, but edges matter. A face shield should wrap well (covering forehead to chin and around toward the ears).", "🌞"),
    ("Face shields are not always a replacement for goggles. For some airborne infection precautions, face shields alone may be insufficient.", "🌞"),
    ("Fit is a major part of protection. Even high-quality PPE works poorly if it sits too far from the face or leaves gaps.", "🌞"),
    ("Markings tell you what a protector is designed to do. Use standards like ANSI/ISEA Z87.1 rather than guessing.", "🌞"),
    ("Keep protective eyewear in good condition. Scratched lenses can reduce clarity, increase glare, and tempt you to remove protection.", "🌞"),
    ("Clean the right way. For coated lenses, harsh chemicals or abrasive wiping can damage coatings; follow manufacturer care instructions.", "🌞"),
    ("Contact lenses do not 'protect' against hazards. For infection control, contacts do not replace PPE.", "🌞"),
    ("In splash or infection-risk work, hand hygiene matters if you wear contacts. Touching lenses with contaminated hands is a known risk pathway.", "🌞"),
    ("If you work around hazards, eye protection should be selected based on a risk assessment matching the specific hazard.", "🌞"),
    ("Eye injuries often happen during 'quick tasks.' People skip PPE for short jobs; wear protection consistently.", "🌞"),
    ("Children and teens also benefit from UV protection outdoors. UV exposure is cumulative across life.", "🌞"),
    
    # 💻 Digital Eye Strain (21-50)
    ("Screen work most often causes symptoms, not 'eye damage.' The common problem is digital eye strain (discomfort), not proven injury.", "💻"),
    ("Digital eye strain has a known symptom cluster: dry/irritated eyes, burning, aching, blurred vision, headaches, and light sensitivity.", "💻"),
    ("A key reason for strain: you blink less when you stare at screens. Less blinking dries the eye surface.", "💻"),
    ("Dryness is often the main driver of discomfort. Strategies targeting tears/blinking frequently help more than 'special lenses.'", "💻"),
    ("Glare makes symptoms worse for many people. Reflections and bright light sources force extra effort and trigger fatigue.", "💻"),
    ("Correct glasses prescription matters. Uncorrected or under-corrected vision makes you strain more at the screen distance.", "💻"),
    ("Your screen position changes eye dryness. Looking straight ahead opens the eyelids more than looking slightly downward.", "💻"),
    ("Taking breaks can help—but it is not magic. The '20-20-20' habit is widely recommended and reduces continuous focusing load.", "💻"),
    ("Blue-light glasses are not strongly supported for eye strain. Reviews found they probably make little or no difference.", "💻"),
    ("Scientific reviews question short-term symptom benefit of blue-light filters. Little to no meaningful reduction versus normal lenses.", "💻"),
    ("'Blue light from screens damages eyes' is not established for normal use. Clinical guidance focuses more on dryness and ergonomics.", "💻"),
    ("Blue light can still matter for sleep timing. Evening screen use can affect circadian rhythms in some people.", "💻"),
    ("Bigger fonts and good contrast reduce strain. If you are squinting or leaning forward, your visual system is working too hard.", "💻"),
    ("Long, unbroken sessions are a common trigger. Symptoms rise with duration and intensity of near work.", "💻"),
    ("Artificial tears can help if dryness is prominent. If symptoms are mostly gritty/burning/dry, lubrication can be very effective.", "💻"),
    ("If you have persistent blur or headaches, get checked. It may be dry eye, an uncorrected refractive error, or binocular issues.", "💻"),
    ("Match screen brightness to the room to reduce discomfort. If your screen is much brighter than surroundings, it causes strain.", "💻"),
    ("Keep the screen about an arm's length away to reduce focusing demand.", "💻"),
    ("Clean your screen; smudges lower contrast and increase visual effort.", "💻"),
    ("Good room lighting reduces harsh contrast between screen and surroundings.", "💻"),
    ("Anti-reflection coatings can reduce distracting reflections on glasses.", "💻"),
    ("Dryness can make contact lenses feel worse during long screen use.", "💻"),
    ("For contact lens wearers with dry eyes, preservative-free artificial tears can help.", "💻"),
    ("Screen position should be slightly below eye level for reduced lid opening and dryness.", "💻"),
    ("Frequent short breaks help more than one long break at the end of work.", "💻"),
    ("The '20-20-20' rule: every 20 minutes, look at something 20 feet away for 20 seconds.", "💻"),
    ("If you get headaches at screens, check both vision correction and ergonomics.", "💻"),
    ("People over ~40 often need near help (presbyopia), and screens can expose it.", "💻"),
    ("Bifocals/progressives may need screen-specific positioning to avoid neck strain.", "💻"),
    ("Dimming screens at night and using warmer tones can improve comfort.", "💻"),
    
    # 💧 Tear Health & Blinking (51-70)
    ("Blinking spreads tears over your eye and keeps the front surface smooth and clear.", "💧"),
    ("People blink less while reading or using screens, which can worsen dryness.", "💧"),
    ("Dry eye can cause burning, gritty feeling, and blurry vision that comes and goes.", "💧"),
    ("Tears are not just water; they have layers that stop fast evaporation.", "💧"),
    ("A fan or AC blowing at your face speeds up tear evaporation.", "💧"),
    ("Low humidity makes dry-eye symptoms worse.", "💧"),
    ("Looking slightly downward at a screen reduces eye surface exposure and dryness.", "💧"),
    ("Frequent blinking and fully closing the lids helps spread the tear film better.", "💧"),
    ("Half-blinks don't spread tears as effectively as complete blinks.", "💧"),
    ("Artificial tears can help dryness; preservative-free options are often better for frequent use.", "💧"),
    ("If your eyes feel gritty in the morning, you might have mild dry eye.", "💧"),
    ("Staying hydrated supports tear production, though it won't fix all dry eye issues.", "💧"),
    ("Omega-3 fatty acids may help some people with dry eye symptoms.", "💧"),
    ("Humidifiers can help in dry indoor environments.", "💧"),
    ("Avoid rubbing your eyes—it can worsen irritation and spread germs.", "💧"),
    ("Warm compresses can help with meibomian gland function and tear quality.", "💧"),
    ("If dry eye persists, see an eye care professional—there are effective treatments.", "💧"),
    ("Some medications can cause or worsen dry eye as a side effect.", "💧"),
    ("Sleeping enough helps eye comfort and tear surface recovery.", "💧"),
    ("Ceiling fans in bedrooms can dry eyes overnight—consider turning them off.", "💧"),
    
    # 🛡️ Safety & Protection (71-85)
    ("For flying particles, safety glasses with side protection reduce injury risk.", "🛡️"),
    ("Contact lenses do not protect against chemicals or impact.", "🛡️"),
    ("For chemical splash risk, sealed goggles are usually safer than open glasses.", "🛡️"),
    ("Eye protection must fit well; gaps reduce real-world protection.", "🛡️"),
    ("Fogging reduces compliance; anti-fog options improve wear time.", "🛡️"),
    ("Industrial/DIY work often causes eye injuries from small fast particles.", "🛡️"),
    ("Chemical exposures should be rinsed immediately with lots of water and treated urgently.", "🛡️"),
    ("Hand hygiene matters; touching eyes can transfer germs and irritants.", "🛡️"),
    ("Allergies can cause itching; treating allergy reduces rubbing and irritation.", "🛡️"),
    ("Rubbing eyes can worsen irritation and, in susceptible people, harm the cornea over time.", "🛡️"),
    ("Welding arcs emit intense UV/visible light and require proper welding filters.", "🛡️"),
    ("Lasers require wavelength- and power-rated eyewear in controlled settings.", "🛡️"),
    ("Snow, water, and sand reflect UV and increase exposure.", "🛡️"),
    ("Acute UV exposure can cause photokeratitis (painful 'sunburn' of the cornea).", "🛡️"),
    ("A brimmed hat adds extra UV protection for eyes and eyelids.", "🛡️"),
    
    # 🌙 Sleep & Circadian (86-100)
    ("Late-night bright screens can shift circadian timing in some people.", "🌙"),
    ("Blue light affects alertness mainly through brightness and timing, not because screens are 'toxic.'", "🌙"),
    ("'Night mode' or reducing screen use before bed may help sleep more reliably than special glasses.", "🌙"),
    ("Consistent sleep schedule supports eye comfort and overall health.", "🌙"),
    ("Darkness at night helps natural melatonin production.", "🌙"),
    ("If you must use screens at night, lower brightness and use warm color settings.", "🌙"),
    ("Reading on paper before bed may be easier on your circadian rhythm than screens.", "🌙"),
    ("Seek urgent care for severe eye pain, sudden vision loss, chemical splash, or new flashes/floaters.", "🌙"),
    ("Regular eye exams catch problems early, even if you feel fine.", "🌙"),
    ("Smoking increases risk of several eye diseases and worsens dryness.", "🌙"),
    ("Wraparound sunglasses reduce UV from the sides and top.", "🌙"),
    ("Eye protection is especially important for children—their lenses let more UV through.", "🌙"),
    ("Many eye conditions are more treatable when caught early.", "🌙"),
    ("If you notice a sudden change in vision, don't wait—get it checked.", "🌙"),
    ("Taking care of your eyes is a long-term investment in quality of life.", "🌙"),
]

# =============================================================================
# ADVANCED TIPS - Witty & insightful eye protection tips
# =============================================================================

ADVANCED_TIPS = [
    # 💧 Blinking & Tears (1-25)
    ("Blinking spreads tears over your eye and keeps the front surface smooth. Your eyes have windshield wipers, but you keep turning them off.", "💧"),
    ("People blink less while reading or using screens, which can worsen dryness. Your laptop is winning the staring contest and your tear glands are losing.", "💧"),
    ("Dry eye can cause burning, gritty feeling, and blurry vision that comes and goes. 'Why is my vision weird?' — because your eyes are doing interpretive dance.", "💧"),
    ("Tears are not just water; they have layers that stop fast evaporation. Your tears are a fancy layered dessert, and office air is the fork.", "💧"),
    ("A fan or AC blowing at your face speeds up tear evaporation. Congratulations to your desk fan for turning moisture into a limited-edition vapor.", "💧"),
    ("Low humidity makes dry-eye symptoms worse. Your eyes didn't sign up for 'indoor desert simulator.'", "💧"),
    ("Looking slightly downward at a screen often reduces eye surface exposure and dryness. Put the screen too high and your eyes start auditioning for the Sahara.", "💧"),
    ("Screens usually cause discomfort (strain/dryness), not eye 'damage' in healthy eyes. Your eyes are complaining loudly, not exploding quietly.", "💧"),
    ("Glare reduces contrast and makes your eyes work harder. Glare is your screen shouting while your eyes whisper, 'Please stop.'", "💧"),
    ("Match screen brightness to the room to reduce discomfort. If your screen can guide ships at night, your eyes will file paperwork.", "💧"),
    ("Bigger text reduces squinting and effort. Large font isn't weakness—it's evidence-based confidence.", "💧"),
    ("Frequent short breaks help more than one heroic break at the end. Tiny breaks are mini-vacations your boss can't tax.", "💧"),
    ("Changing focus distance helps your focusing system relax. Your eye muscles deserve a stretch, not a lifetime contract.", "💧"),
    ("The '20-20-20' habit is a practical reminder to rest and refocus. It's not magic—it's just letting your eyeballs see something that isn't a spreadsheet.", "💧"),
    ("Keep the screen about an arm's length away to reduce focusing demand. If you're nose-to-screen, your eyes are doing close-up comedy without consent.", "💧"),
    ("Clean your screen; smudges lower contrast and increase effort. Your eyes shouldn't have to solve a mystery film of fingerprints.", "💧"),
    ("Good room lighting reduces harsh contrast between screen and surroundings. Your eyes prefer 'pleasant café,' not 'cave with a glowing rectangle.'", "💧"),
    ("Anti-reflection coatings can reduce distracting reflections. Reflections are like pop-up ads, but for photons.", "💧"),
    ("Dryness can make contact lenses feel worse during long screen use. Contacts plus screens can be a buddy-cop movie where both cops hate the job.", "💧"),
    ("Contact lenses do not protect against chemicals or impact. Contacts don't block danger; they just give it a place to sit.", "💧"),
    ("For chemical splash risk, sealed goggles are usually safer than open glasses. If splashes are possible, 'almost covered' is not a comforting phrase.", "💧"),
    ("For flying particles, safety glasses with side protection reduce injury risk. Side shields: because debris rarely attacks from the front like a polite villain.", "💧"),
    ("Regular fashion glasses are not guaranteed impact protection. They help you see the problem clearly right before it hits you.", "💧"),
    ("Eye protection must fit well; gaps reduce real-world protection. Safety gear that doesn't fit is cosplay with consequences.", "💧"),
    ("Fogging reduces compliance; anti-fog options improve wear time. Foggy goggles turn you into a cautious penguin.", "💧"),
    
    # 🌞 UV & Sunlight (26-50)
    ("UV light from the sun is a major long-term risk for eyes. The sun is bright, powerful, and absolutely not your friend's chill lamp.", "🌞"),
    ("Choose sunglasses that block UVA and UVB (often labeled UV400). Think of it as a bouncer for bad photons.", "🌞"),
    ("Dark tint without UV blocking can be risky because pupils may dilate. Some sunglasses are just stylish lies with attitude.", "🌞"),
    ("Wraparound sunglasses reduce UV from the sides and top. Sunlight loves sneaking in from angles like it owns the place.", "🌞"),
    ("A brimmed hat adds extra UV protection for eyes and eyelids. It's sunscreen for your face, but in hat form.", "🌞"),
    ("Snow, water, and sand reflect UV and increase exposure. Nature invented mirrors and immediately used them for chaos.", "🌞"),
    ("Acute UV exposure can cause photokeratitis (painful 'sunburn' of the cornea). Yes, your eyeball can get sunburned; biology is dramatic.", "🌞"),
    ("Welding arcs emit intense UV/visible light and require proper welding filters. Welding without proper protection is a speedrun to regret.", "🌞"),
    ("Lasers require wavelength- and power-rated eyewear in controlled settings. 'It looks cool' is not a safety protocol.", "🌞"),
    ("Industrial/DIY work often causes eye injuries from small fast particles. Tiny things moving fast: the universe's favorite way to cause problems.", "🌞"),
    ("Chemical exposures should be rinsed immediately with lots of water and treated urgently. If chemicals meet eyeballs, the plan is 'flush now,' not 'Google later.'", "🌞"),
    ("Hand hygiene matters; touching eyes can transfer germs and irritants. Your hands have been places your corneas should never visit.", "🌞"),
    ("Allergies can cause itching; treating allergy reduces rubbing and irritation. Your eyes aren't asking for a wrestling match—they're asking for relief.", "🌞"),
    ("Rubbing eyes can worsen irritation and, in susceptible people, harm the cornea over time. Your cornea would like you to stop 'massaging' it with rage.", "🌞"),
    ("Sleeping enough helps eye comfort and surface recovery. Sleep is the nightly software update you keep hitting 'remind me later' on.", "🌞"),
    ("Late-night bright screens can shift circadian timing in some people. Your brain sees midnight TikTok as 'excellent morning sunlight.'", "🌞"),
    ("Dimming screens at night and using warmer tones can improve comfort for some users. Make your screen less 'interrogation lamp' and more 'cozy candle.'", "🌞"),
    ("Blue light affects alertness mainly through brightness and timing, not because screens are 'toxic.' The real villain is 'bright at midnight,' not 'blue exists.'", "🌞"),
    ("If you get headaches at screens, check vision correction and ergonomics. Your eyes may be doing extra math because your glasses are off by a tiny but evil amount.", "🌞"),
    ("People over ~40 often need near help (presbyopia), and screens can expose it. Welcome to the 'my arms aren't long enough' expansion pack.", "🌞"),
    ("Bifocals/progressives may need screen-specific positioning to avoid neck strain. If your neck hurts, your glasses might be trolling you.", "🌞"),
    ("Frequent blinking and fully closing the lids helps spread the tear film better. Half-blinks are like washing dishes by thinking about soap.", "🌞"),
    ("Artificial tears can help dryness; preservative-free options are often better for frequent use. Think of it as moisturiser for your eyeballs—less glamorous, more effective.", "🌞"),
    ("Smoking increases risk of several eye diseases (including cataracts) and worsens dryness. Smoking: somehow bad for lungs and for your eyeballs—multitalented in the worst way.", "🌞"),
    ("Seek urgent care for severe eye pain, sudden vision loss, chemical splash, or new flashes/floaters. If your vision suddenly goes weird, do not 'walk it off'—eyes are not ankles.", "🌞"),
    
    # 💻 Screen Wisdom (51-75)
    ("Your screen brightness should match your environment. A screen brighter than the sun at midnight is not 'vivid'—it's an interrogation.", "💻"),
    ("Blue light filters probably don't reduce eye strain, but they might help you sleep if used at night. Science says: meh for eyes, maybe for bedtime.", "💻"),
    ("The '20-20-20' rule won't cure everything, but it's free and low-risk. It's basically yoga for your eyeballs.", "💻"),
    ("Positioning your screen below eye level reduces the exposed surface of your eye. Geometry: protecting your tear film since forever.", "💻"),
    ("If you're leaning forward to read, your font is too small. Your spine and eyes are forming a union.", "💻"),
    ("A dirty screen is a workout your eyes didn't ask for. Cleaning it takes 30 seconds; squinting takes hours.", "💻"),
    ("Reflections on your screen make your brain work overtime. It's like reading while someone waves a flashlight at you.", "💻"),
    ("The best lighting for screen work is even and indirect. 'Dramatic shadows' are for movies, not spreadsheets.", "💻"),
    ("If your eyes feel tired by noon, something in your setup is wrong. Eyes shouldn't feel like they ran a marathon by lunch.", "💻"),
    ("Artificial tears are underrated for screen workers. They're cheap, safe, and your tear film will thank you.", "💻"),
    ("Taking breaks isn't slacking—it's maintenance. Your eyes don't have a 'push through it' setting.", "💻"),
    ("If you wear contacts and stare at screens, you're on hard mode for dry eye. Glasses are sometimes the MVP.", "💻"),
    ("Night mode on your devices won't save your eyes, but it might save your sleep. Priorities, people.", "💻"),
    ("Looking out a window isn't just nice—it lets your focusing muscles actually relax. It's free therapy for your ciliary body.", "💻"),
    ("If one eye feels worse than the other, that's worth investigating. Eyes are supposed to be a team.", "💻"),
    ("Headaches from screen work often come from uncorrected vision or poor ergonomics. Your head is a symptom, not the problem.", "💻"),
    ("Reading on a tablet in bed is cozy until your sleep schedule becomes abstract art.", "💻"),
    ("E-ink displays cause less eye strain for long reading because they don't glow at you. Paper's digital cousin.", "💻"),
    ("A second monitor can reduce strain by letting you avoid constant window-switching. Efficiency for your eyeballs.", "💻"),
    ("If you wear progressives, you might need 'computer glasses' for the right focal distance. Your lenses shouldn't make you a bobblehead.", "💻"),
    ("The best screen position is where you don't have to tilt your head. Your neck and eyes should both be comfortable.", "💻"),
    ("Text contrast matters—light gray on white is not 'elegant,' it's 'squint-inducing.'", "💻"),
    ("If you're getting eye strain, check your prescription first. Outdated glasses are working against you.", "💻"),
    ("Laptop screens are often too low for good ergonomics. A stand or external monitor can help.", "💻"),
    ("Split-screen work is efficient but makes text smaller. Zoom in or your eyes will zoom out (to the optometrist).", "💻"),
    
    # 🦉 Owl Wisdom (76-100)
    ("Your eyes don't have a warranty, but they do respond to maintenance. Small habits add up.", "🦉"),
    ("The best eye protection is the one you actually use. Fancy gear in a drawer protects nothing.", "🦉"),
    ("If you skip eye exams because 'you see fine,' you might be missing things you can't see yet. Irony.", "🦉"),
    ("Eye problems often develop slowly—regular checkups catch what you won't notice.", "🦉"),
    ("Children's eyes are more vulnerable to UV because their lenses are clearer. Start sunglasses early.", "🦉"),
    ("Most eye injuries are preventable with proper protection. The 'it'll be fine' approach has bad statistics.", "🦉"),
    ("If your eyes are red and itchy every spring, that's allergies, not just 'tired eyes.' Treatment exists.", "🦉"),
    ("Dry eye is common and treatable—don't just suffer through it. Talk to a professional.", "🦉"),
    ("If you see floaters or flashes suddenly, get checked urgently. Retinas don't announce problems politely.", "🦉"),
    ("Your lifestyle affects your eyes: sleep, hydration, and not rubbing them all matter.", "🦉"),
    ("Eyes are the only part of your central nervous system directly exposed to the world. Treat them accordingly.", "🦉"),
    ("Good habits now prevent expensive problems later. Your future self will appreciate current you.", "🦉"),
    ("Eye care isn't just about seeing—it's about comfort, too. Chronic discomfort deserves attention.", "🦉"),
    ("If one eye suddenly sees worse than the other, that's never 'probably nothing.'", "🦉"),
    ("Screen time isn't evil, but unbroken screen time is unkind to your eyes.", "🦉"),
    ("Your eyes work hard for you—give them breaks, moisture, and protection in return.", "🦉"),
    ("The 'I'll deal with it later' approach to eye symptoms often makes things harder to fix.", "🦉"),
    ("Eye strain is your body's feedback system. Ignoring it doesn't make it wrong—just louder.", "🦉"),
    ("A few seconds of eye care throughout the day beats emergency repairs later.", "🦉"),
    ("Your environment matters: lighting, humidity, and screen setup all affect eye comfort.", "🦉"),
    ("If you need glasses, wear them. Squinting is not a superpower.", "🦉"),
    ("Taking care of your eyes is self-respect in a very literal, biological sense.", "🦉"),
    ("Eyes are complex and mostly self-maintaining—help them out with simple habits.", "🦉"),
    ("Prevention is cheaper and easier than treatment. Your eyes agree.", "🦉"),
    ("The owl says: blink more, take breaks, protect from UV, and see a professional regularly. Wisdom delivered.", "🦉"),
]

# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def get_tip_count(is_exceptional: bool = False) -> int:
    """Get the total number of tips available."""
    return len(ADVANCED_TIPS) if is_exceptional else len(NORMAL_TIPS)


def get_tip_by_index(index: int, is_exceptional: bool = False) -> Tuple[str, str]:
    """
    Get a specific tip by index.
    
    Returns:
        tuple: (tip_text, category_emoji)
    """
    tips_list = ADVANCED_TIPS if is_exceptional else NORMAL_TIPS
    index = index % len(tips_list)
    return tips_list[index]
