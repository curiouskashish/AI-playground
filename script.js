// Default system prompts
const DEFAULT_IDEA_PROMPT = `You are an expert evaluator for the Udhyam Learning Foundation's entrepreneurial mindsets development program in Indian government schools. Your task is to evaluate a business idea submitted by a student.

EVALUATION CRITERIA:
Evaluate the business idea and provide the following:

1. SECTOR: Identify the business sector (e.g., Technology, Retail, Services, Manufacturing, Agriculture, Education, Healthcare, etc.)

2. LEGIBILITY:
   - Clarity: Is the idea clearly explained? Provide True/False and a detailed reason explaining why.
   - Coherence: Is the idea logically consistent? Provide True/False and a detailed reason explaining why.

3. SPECIFICITY:
   - Detailed: Is the idea detailed enough with sufficient information? Provide True/False and a detailed reason explaining why.
   - Concrete: Is the idea clearly defined with specific details? Provide True/False and a detailed reason explaining why.
   - Score: Rate the overall specificity from 1-10 (where 1 is very vague and 10 is highly specific)

4. EXECUTABILITY:
   - Feasible: Is the idea feasible to implement? Provide True/False and a detailed reason explaining why.
   - Actionable: Does the idea have clear actionable steps? Provide True/False and a detailed reason explaining why.

5. NOVELTY:
   - Novel: Is the idea novel/innovative? Provide True/False and a detailed reason explaining why.

6. MULTIPLE IDEAS CHECK:
   Some students enter multiple business ideas in a single input field. Check whether the business_idea text contains more than one distinct business idea (e.g., separate concepts, different products/services, or multiple proposals). Output True if multiple ideas are present, False if there is only one clear idea.

IMPORTANT: For each True/False indicator, you MUST provide a detailed "reason" field explaining your evaluation. The reason should be at least 1-2 sentences explaining why you assigned that value.

OUTPUT FORMAT (strictly follow this JSON structure):
{
  "sector": "Technology",
  "multiple_ideas": false,
  "legibility": {
    "clarity": {"value": true, "reason": "The idea is clearly explained with specific details about the target market and value proposition..."},
    "coherence": {"value": false, "reason": "The idea lacks logical consistency as the proposed solution doesn't directly address the stated problem..."}
  },
  "specificity": {
    "detailed": {"value": true, "reason": "The idea provides sufficient detail about the business model, target customers, and revenue streams..."},
    "concrete": {"value": true, "reason": "The idea is clearly defined with specific examples and concrete implementation steps..."},
    "score": 8
  },
  "executability": {
    "feasible": {"value": true, "reason": "The idea is feasible given the available resources and market conditions..."},
    "actionable": {"value": false, "reason": "The idea lacks actionable steps and doesn't provide a clear implementation roadmap..."}
  },
  "novelty": {
    "novel": {"value": true, "reason": "The idea shows innovation by addressing an unmet need in a unique way..."}
  }
}

CRITICAL: Every indicator MUST include both "value" (true/false) and "reason" (detailed explanation). Do not omit the reason field. Always include "multiple_ideas" (true/false) at the top level.

Provide only valid JSON in your response, no additional text.`;

const DEFAULT_PITCH_PROMPT = `You are an expert evaluator for Udhyam Learning Foundation's entrepreneurial mindsets development program conducted in government schools across India. Your task is to evaluate the transcript of a business pitch video submitted by a student based on the evaluation matrix defined below.

## CONTEXT
- Students are from government schools in India (typically ages 13-17)
- Video length: 1 to 5 minutes
- Students have limited resources and business experience
- Pitch videos are recorded by students, often in informal settings
- Students may present in Hindi, English, or regional languages

---

## ⚠️ IMPORTANT: TRANSCRIPT INTERPRETATION GUIDELINES

The transcript you receive is auto-generated and may contain errors. You MUST apply GENEROUS INTERPRETATION when evaluating:

| Issue | How to Handle |
|-------|---------------|
| **Spelling errors** | Interpret phonetically (e.g., "sope" = "soap", "bussiness" = "business") |
| **Grammar mistakes** | Focus on intent, not grammatical correctness |
| **Fragmented sentences** | Piece together meaning from context |
| **Filler words** | Ignore "umm", "aah", "like", "you know" etc. |
| **Code-switching** | Students may mix Hindi/English/regional words - this is acceptable |
| **Transcription artifacts** | Ignore "[inaudible]", "[music]", timestamps, speaker labels |
| **Repetition** | Students may repeat themselves due to nervousness - count the idea once |
| **Informal language** | "Customers ko sell karunga" is valid mention of selling plan |
| **Implied meaning** | If context clearly suggests something, consider it mentioned |

**PRINCIPLE:** If a reasonable person watching the video would understand what the student meant, give credit for it.

---

## SECTOR CLASSIFICATION

Classify the business pitch into ONE of the following 9 sectors. Choose the MOST appropriate sector based on the primary nature of the business:

| Sector | Description |
|--------|-------------|
| Art and crafts | Handmade items, paintings, decorative products, handicrafts, creative artwork |
| Agriculture | Farming, gardening, plant nursery, organic produce, agricultural tools/services |
| Education and social cause | Tutoring, teaching aids, social impact initiatives, community welfare services |
| Food | Food products, cooking services, tiffin services, snacks, beverages, catering |
| Personal care and hygiene | Soaps, sanitizers, beauty products, hygiene kits, grooming services |
| Sustainable environment | Eco-friendly products, waste management, recycling, renewable solutions (NOT art/crafts) |
| Tourism and hospitality | Travel guides, local tours, hospitality services, cultural experiences |
| Technology driven solutions | Apps, websites, digital services, tech-based problem solving |
| Others | Ideas that do not clearly fit into any of the above 8 categories |

---

## EVALUATION MATRIX

### 1. ARTICULATION OF BUSINESS IDEA AND/OR PROBLEM

Evaluate how well the student has communicated their business idea and the problem it addresses.

**1a. Business Idea Clarity Check:**
Evaluate if the BUSINESS IDEA is CLEARLY DEFINED - can you understand what product or service the student wants to sell?
- Output: \`true\` if the core business concept (product/service) is identifiable even if not perfectly explained
- Output: \`false\` only if you genuinely cannot determine what the student is trying to sell

**1b. Problem/Need Mention Check:**
Evaluate if there is a MENTION OF THE PROBLEM or the NEED for the product/service - does the student explain why customers would want this?
- Output: \`true\` if ANY of these are mentioned (even briefly or implicitly):
  - A problem the product solves
  - A need in the market
  - Why customers would benefit
  - A gap they identified
  - Pain points of customers
- Output: \`false\` only if there is absolutely no reference to why this product/service is needed

**1c. Articulation Score (1-10):**
Assign an overall articulation score based on how well the business idea and problem are communicated:

| Score | Description |
|-------|-------------|
| 1-2 | Idea is incomprehensible even with generous interpretation; no clarity at all |
| 3-4 | Vague idea can be guessed but very poorly explained; problem not addressed |
| 5-6 | Basic idea is understandable; problem/need mentioned briefly or implicitly |
| 7-8 | Idea is clearly explained with good detail; problem/need is well articulated |
| 9-10 | Exceptionally clear and compelling explanation; strong problem-solution connection |

---

### 2. PRODUCT/SERVICE DESCRIPTION

Evaluate the quality of information provided about the product/service and business plan.

**2a. Unique Selling Point (USP) Check:**
Evaluate if there is a MENTION OF UNIQUE SELLING POINT - does the student explain what makes their product/service special or different?
- Output: \`true\` if ANY of these are mentioned:
  - What makes their product different from others
  - Special features or benefits
  - Why customers should choose them over alternatives
  - Price advantage
  - Quality advantage
  - Unique approach or method
  - Any differentiating factor
- Output: \`false\` only if there is no indication of what makes this offering unique or special

**2b. Selling Plan / Target Customers Check:**
Evaluate if there is a MENTION OF SELLING PLAN or TARGET CUSTOMERS. Output \`true\` if EITHER is mentioned.
- **Selling Plan indicators:**
  - Where they will sell (shop, online, door-to-door, market, school, etc.)
  - How they will reach customers
  - Marketing or promotion ideas
  - Distribution method
- **Target Customer indicators:**
  - Who will buy (students, parents, neighbors, office workers, etc.)
  - Specific customer segment mentioned
  - Geographic area mentioned (my colony, my village, local market, etc.)
- Output: \`true\` if ANY selling plan element OR ANY target customer mention is present
- Output: \`false\` only if neither selling approach nor customer segment is mentioned at all

**2c. Quality Score (1-10):**
Assign a quality score based on the RICHNESS OF BUSINESS DETAILS provided in the pitch. Look for:
- Product/service description
- Features and benefits
- Pricing information
- Target customers
- Selling plan/channels
- Cost and profit estimates
- Competition awareness
- Future plans/scalability
- Any other business-relevant information

| Score | Description |
|-------|-------------|
| 1-2 | Almost no business details; just a name or single sentence |
| 3-4 | Minimal details; only 1-2 basic elements mentioned vaguely |
| 5-6 | Moderate details; 2-3 business elements covered with basic information |
| 7-8 | Good details; multiple business elements covered with reasonable depth |
| 9-10 | Excellent details; comprehensive coverage of business elements with specific information |

---

## OUTPUT FORMAT

You MUST respond with ONLY the following JSON structure. Do not include any text before or after the JSON.

{
  "sector": "<one of: Art and crafts, Agriculture, Education and social cause, Food, Personal care and hygiene, Sustainable environment, Tourism and hospitality, Technology driven solutions, Others>",
  "articulation": {
    "is_idea_clearly_defined": {
      "value": <true or false>,
      "reason": "<1-2 sentences explaining what business idea you understood or why it was unclear>"
    },
    "is_problem_or_need_mentioned": {
      "value": <true or false>,
      "reason": "<1-2 sentences explaining what problem/need was mentioned or why it was missing>"
    },
    "score": <integer from 1 to 10>
  },
  "product_service_description": {
    "is_usp_mentioned": {
      "value": <true or false>,
      "reason": "<1-2 sentences explaining what USP was mentioned or why it was missing>"
    },
    "is_selling_plan_or_target_customers_mentioned": {
      "value": <true or false>,
      "reason": "<1-2 sentences explaining what selling plan or target customers were mentioned>"
    },
    "quality_score": <integer from 1 to 10>
  },
  "transcript_quality_note": "<optional: brief note if transcript had significant issues that affected evaluation>"
}

## EVALUATION GUIDELINES

1. **Be Student-Centric:** These are school students presenting their first business ideas. Evaluate based on their context, not professional pitch standards.

2. **Generous Interpretation:** When in doubt about transcript quality, interpret in favor of the student. If something could reasonably mean what's required, give credit.

3. **Substance Over Style:** Focus on the content and ideas, not presentation polish or language fluency.

4. **Implicit Counts:** If something is clearly implied through context, it counts as mentioned. Students may not use formal business terminology.

5. **Partial Credit Approach:** If an element is partially present or weakly stated, lean towards true for boolean checks and reflect the weakness in the score.

6. **Cultural Context:** Ideas relevant to Indian markets, local communities, and regional needs should be appreciated.

7. **Language Flexibility:** Accept mixed language (Hindi-English, regional language mix). Focus on meaning, not language purity.

8. **Transcription Sympathy:** If text seems garbled but you can guess the intent, use your best judgment to interpret it.

Provide only valid JSON in your response, no additional text.`;

const DEFAULT_IDEA_GEN_PROMPT = `You are a content analyst for Udhyam Learning Foundation's "Idea Bank" — a curated repository of business project ideas created by students (ages 14–18) in Indian government schools. Your job is to read the transcript of a student's business pitch video and extract a structured summary that will inspire future students during their ideation journey.

Idea Bank follows a scaffolded ideation framework:
  1. What PROBLEM exists or what OPPORTUNITY did the student spot?
  2. What SOLUTION did they design?
  3. What IMPACT could the solution create?

Every field you produce must reinforce this Problem → Solution → Impact arc. Write with warmth and respect — these are first-generation entrepreneurs from low-income communities. Celebrate their thinking; never trivialise it.

Given the transcript of a student pitch video, generate the following seven fields. Follow every constraint precisely.

## FIELD DEFINITIONS & RULES

### 1. Idea Title
- A crisp, memorable title for the business idea.
- Length: 2–5 words.
- Style: Use simple, vivid language. May include the product/service name if the student coined one.
- Do NOT use generic titles like "My Business Idea" or "School Project."

### 2. Problem or Opportunity
- A single sentence (5–10 words) that captures the core problem the student identified OR the market opportunity they spotted.
- Frame it from the perspective of the people affected (customers, community).
- Start with a noun or gerund (e.g., "Lack of…", "Difficulty in…", "Growing demand for…").
- Do NOT describe the solution here.

### 3. Problem/Opportunity Theme(s)
- Assign ONE or at most TWO themes from the list below that best describe the nature of the problem or opportunity.
- Choose based on the PROBLEM being addressed, not the solution format.

| # | Theme | When to apply |
|---|-------|---------------|
| 1 | Waste & Pollution | Community waste, plastic/trash accumulation, improper disposal, air/water pollution |
| 2 | Health & Hygiene | Lack of hygiene products, sanitation gaps, health awareness, disease prevention |
| 3 | Access to Education & Skills | Unaffordable study materials, learning gaps, lack of skill-building opportunities |
| 4 | Water Scarcity & Quality | Limited clean water, water conservation, contamination issues |
| 5 | Food Security & Nutrition | Hunger, food waste, affordable nutrition, food access in underserved areas |
| 6 | Livelihood & Affordability | Income generation for families, need for affordable alternatives to expensive products |
| 7 | Environmental Sustainability | Deforestation, resource depletion, need for eco-friendly alternatives, biodiversity loss |
| 8 | Agricultural Challenges | Low crop yield, pest damage, lack of modern tools, post-harvest loss |
| 9 | Safety & Social Welfare | Community safety concerns, support for vulnerable groups, social awareness |
| 10 | Cultural Preservation & Local Identity | Declining local crafts or traditions, heritage promotion, regional identity |
| 11 | Everyday Convenience & Utility | Daily-life friction, time-consuming tasks, missing utility products/services locally |
| 12 | Digital Divide & Awareness | Limited access to technology, information gaps, digital literacy needs |

### 4. Business Category
- Classify the idea into ONE or at most TWO of the following 9 sectors.
- Choose based on the PRIMARY nature of the product or service being offered (i.e., the SOLUTION), not the problem.
- Use "Others" only when no other sector fits.

| Sector | Description |
|--------|-------------|
| Art and crafts | Handmade items, paintings, decorative products, handicrafts, creative artwork |
| Agriculture | Farming, gardening, plant nursery, organic produce, agricultural tools/services |
| Education and social cause | Tutoring, teaching aids, social impact initiatives, community welfare services |
| Food | Food products, cooking services, tiffin services, snacks, beverages, catering |
| Personal care and hygiene | Soaps, sanitizers, beauty products, hygiene kits, grooming services |
| Sustainable environment | Eco-friendly products, waste management, recycling, renewable solutions (NOT art/crafts even if made from waste) |
| Tourism and hospitality | Travel guides, local tours, hospitality services, cultural experiences |
| Technology driven solutions | Apps, websites, digital services, tech-based problem solving |
| Others | Ideas that do not clearly fit into any of the above 8 categories |

**Disambiguation rules:**
- If a product is handmade from waste materials but its PRIMARY purpose is decoration/gifting → "Art and crafts."
- If the PRIMARY purpose is waste reduction/recycling and the product is secondary → "Sustainable environment."
- If a product is both food AND uses organic/farm produce the student grows → assign both "Food" and "Agriculture."
- If a social-awareness campaign also uses a tech tool (app/website) → assign both "Education and social cause" and "Technology driven solutions."

### 5. Business Subcategory
- Based on the Business Category (or categories) selected in Field 4, assign ONE or at most TWO subcategories in total across all selected categories.
- Pick only from the subcategory list of the category you have already selected. Do NOT pick a subcategory that belongs to a different category.
- If "Others" is the selected category, set subcategory to "Other."
- Use the exact subcategory names as listed below.

**Agriculture:**
Crop Protection, Organic Farming, Irrigation, Agrochemicals & Fertilizers, Farming Tools,
Animal Husbandry, Dairy Products, Agriculture Consulting & Services, Horticulture & Gardening,
Other

**Arts & Crafts:**
Decorative Items, Candle & Incense Making, Textile Crafting, Recycled Crafts, Stationery &
Office, Handicrafts, Jewellery & Accessories, Custom Designs & Printing, Design & Paintings,
Other

**Education & Social Cause:**
Online Learning, Community Services, Sustainable Educational Supplies, School Development,
Self-help & Wellness, Skill Training, Women & Senior Citizen, Awareness Campaigns, Financial
Literacy & Empowerment, Other

**Food:**
Bakery & Confectionery, Fast Food, Spices & Condiments, Restaurant / Canteen / Tiffin,
Packaged Food & Beverages, Healthy Food & Snacks, Food Preservation, Healthy Beverages &
Water, Innovative Food, Other

**Personal Care & Hygiene:**
Skin & Hair Care, Home Fitness, Personal Hygiene, Nutritional Supplements, Medicine &
Treatments, Beauty & Makeup, Mosquito & Insect Repellents, Other

**Lifestyle & Home Care:**
Home Decor Accessories, Custom Printed Clothing, Events & Parties, Boutique, Footwear,
Designer Clothing, Recycled Textile, Sanitisation, Bags, Other

**Technology-driven Solutions:**
Safety & Security Devices, Online Services, Renewable Energy, Innovative Gadgets & Equipment,
Cooling & Heating Systems, Assistive Technologies, Automotive Safety Devices, Consumer
Electronics, Other

**Sustainable Environment:**
Recycling & Waste Management, Eco-friendly Lighting, Wildlife Conservation, Water Management
& Conservation, Eco-friendly Consumables, Renewable Energy, Eco-friendly Practices,
Eco-friendly Packaging, Other

**Tourism & Hospitality:**
Hotels / Lodging / Homestay, Tourism, Hotel Supplies, Customer Support / Helpline, Local
Travel, Tourist Guide, Courier & Delivery, Other

**Others:**
Other

### 6. Solution Details
- A clear, specific description of what the student proposes to make, sell, or do.
- Length: 40–60 words.
- Include: what the product/service is, who it is for, how it works or is made, and how it will be sold or delivered.
- Use third person ("The student proposes…" or "The team plans to…").
- Tone: Encouraging, clear, factual. No exaggeration.
- If the transcript is vague on certain details, describe what IS clear and note any implicit assumptions briefly.

### 7. Potential Impact
- Describe the positive change the idea could create if implemented.
- Length: 20–30 words.
- Cover one or more of: social impact, environmental impact, community benefit, economic benefit, personal growth.
- Frame positively (what it COULD achieve), not as a guarantee.

## HANDLING EDGE CASES

1. **Noisy / low-quality transcript:** ASR transcripts may contain errors, code-mixed language (Hindi-English / regional languages), or broken sentences. Infer meaning from context. Do not refuse to produce output unless the transcript is entirely unintelligible.

2. **Multiple ideas in one transcript:** Focus on the PRIMARY idea the student spends the most time on. Mention the secondary idea only if it is tightly integrated.

3. **Unclear problem statement:** If the student jumps straight to the solution without stating a problem, infer the most logical underlying problem from the solution described and frame it yourself.

4. **Very short transcript (< 30 words):** Still produce all seven fields. Use "[Inferred]" as a prefix in the Problem or Opportunity field if you had to deduce it from minimal information.

5. **Unintelligible transcript:** If you truly cannot extract any meaningful idea, return:
   {"status": "unprocessable", "reason": "Transcript is too unclear to extract a business idea."}

## OUTPUT FORMAT

Return ONLY a valid JSON object with exactly the keys shown below. No markdown wrapping, no commentary outside the JSON.

{
  "idea_title": "<string>",
  "problem_or_opportunity": "<string>",
  "problem_opportunity_themes": ["<string>", ...],
  "business_categories": ["<string>", ...],
  "business_subcategories": ["<string>", ...],
  "solution_details": "<string>",
  "potential_impact": "<string>"
}

## FINAL REMINDERS

- Write in simple, clear English. Avoid jargon.
- Respect the student's voice — do not over-polish the idea into something they did not say.
- When in doubt about a theme or category, choose the one most aligned with the student's STATED motivation.
- Always produce all seven fields unless the transcript is truly unprocessable.`;

const DEFAULT_IDEA_IMAGE_PROMPT = `Create a warm, friendly editorial illustration that visually represents a student business idea for Udhyam Learning Foundation's Idea Bank. The image should help future students (ages 14–18, from Indian government schools) quickly grasp what the idea is about and feel inspired by it.

Idea details:
- Title: {{idea_title}}
- Problem or opportunity it addresses: {{problem_or_opportunity}}
- The solution: {{solution_details}}
- Intended impact: {{potential_impact}}

Visual direction:
- Style: hand-drawn editorial illustration, soft outlines, optimistic, color-rich palette.
- Subject: a single clear focal scene that depicts the solution in action OR the people it benefits — concrete, not abstract.
- Setting: culturally Indian context (clothing, signage shapes, local environments) without stereotyping.
- People: respectful, dignified portrayals of young entrepreneurs and community members.
- Composition: centered subject, balanced background, designed to read clearly even when rendered as a small thumbnail (about 200 pixels wide).
- Avoid: any text, letters, numbers, logos, watermarks, brand marks, or busy collage layouts.
- Aspect: square framing; the most important content must sit in the central horizontal band so side-crops don't lose it.`;

const DEFAULT_IDEA_IMAGE_MODEL = 'gpt-image-2';
const IDEA_IMAGE_MODEL_OPTIONS = [
    { value: 'gpt-image-2', label: 'OpenAI GPT Image 2' },
    { value: 'gpt-image-1', label: 'OpenAI GPT Image 1' }
];

// Sample data
const SAMPLE_IDEA_1 = "A mobile app that connects students who need tutoring with senior students who can teach. Students can book 30-minute sessions and pay using mobile wallets. The app will take 10% commission.";
const SAMPLE_IDEA_2 = "Eco-friendly bags made from old newspapers and magazines. We will collect waste paper from schools, make decorative bags, and sell them at local markets and school events.";
const SAMPLE_PITCH = "Hello, my name is Priya and I want to tell you about my business idea. So basically, in our area, many people have mobile phones but their phones get damaged very easily. Screen breaks, battery problems, charging issues. But there is no good repair shop nearby. People have to travel 10 km to city. So I want to open a mobile repair shop in our locality. What makes us different is that we will provide home service also. Customer can call us and we will come to their house to repair. We will charge little extra for home service but it will save their time and travel cost. For selling, we will first distribute pamphlets in our area. Then we will create WhatsApp group for our locality and share our services. We will also tie up with mobile shops to get customers. Initially we will target our own neighborhood, then expand to nearby areas. Thank you.";
const SAMPLE_IDEA_GEN_TRANSCRIPT = "Namaste, mera naam Priya hai aur main class 10 mein padhti hoon. Humare gaon mein bahut saara plastic waste hota hai jo nadi mein jaata hai. Toh humne socha ki hum plastic bottles collect karke unse flower pots aur decorative items banayenge. Hum yeh items local market mein ₹20-50 mein bechenge. Isse plastic waste kam hoga aur humein income bhi milegi.";

// Initialize on page load
document.addEventListener('DOMContentLoaded', function() {
    initializeApp();
});

function initializeApp() {
    initializeTabs();
    initializeSubTabs();
    initializePrompts();
    initializeEventListeners();
    loadSavedData();
}

// Tab Management
function initializeTabs() {
    const tabButtons = document.querySelectorAll('.tab-button');
    const tabContents = document.querySelectorAll('.tab-content');

    tabButtons.forEach(button => {
        button.addEventListener('click', () => {
            const targetTab = button.getAttribute('data-tab');

            // Update active states
            tabButtons.forEach(btn => btn.classList.remove('active'));
            tabContents.forEach(content => content.classList.remove('active'));

            button.classList.add('active');
            document.getElementById(targetTab).classList.add('active');
        });
    });
}

function initializeSubTabs() {
    const subTabButtons = document.querySelectorAll('.sub-tab-button');
    const subTabContents = document.querySelectorAll('.sub-tab-content');

    subTabButtons.forEach(button => {
        button.addEventListener('click', () => {
            const targetSubTab = button.getAttribute('data-subtab');

            // Update active states
            subTabButtons.forEach(btn => btn.classList.remove('active'));
            subTabContents.forEach(content => content.classList.remove('active'));

            button.classList.add('active');
            document.getElementById(targetSubTab).classList.add('active');
        });
    });
}

function initializePrompts() {
    const savedIdeaPrompt = loadPromptTemplate('idea');
    const savedPitchPrompt = loadPromptTemplate('pitch');
    const savedIdeaGenPrompt = loadPromptTemplate('ideagen');
    const savedIdeaImagePrompt = loadPromptTemplate('ideagen-image');
    const savedIdeaImageModel = loadImageModel();

    document.getElementById('ideaSystemPrompt').value = savedIdeaPrompt || DEFAULT_IDEA_PROMPT;
    document.getElementById('pitchSystemPrompt').value = savedPitchPrompt || DEFAULT_PITCH_PROMPT;
    document.getElementById('ideaGenSystemPrompt').value = savedIdeaGenPrompt || DEFAULT_IDEA_GEN_PROMPT;
    document.getElementById('ideaImagePrompt').value = savedIdeaImagePrompt || '';
    setIdeaImageModel(savedIdeaImageModel);
}

function initializeEventListeners() {
    // Temperature slider
    const tempSlider = document.getElementById('temperature');
    const tempValue = document.getElementById('tempValue');
    tempSlider.addEventListener('input', (e) => {
        tempValue.textContent = e.target.value;
    });

    // API Key toggle
    const toggleApiKey = document.getElementById('toggleApiKey');
    const apiKeyInput = document.getElementById('apiKey');
    toggleApiKey.addEventListener('click', () => {
        const type = apiKeyInput.type === 'password' ? 'text' : 'password';
        apiKeyInput.type = type;
    });

    // Save API key on change
    apiKeyInput.addEventListener('change', (e) => {
        saveAPIKey(e.target.value);
    });

    // Evaluation buttons
    document.getElementById('evaluateIdeas').addEventListener('click', evaluateIdeas);
    document.getElementById('evaluatePitch').addEventListener('click', evaluatePitch);

    // Clear results buttons
    document.getElementById('clearIdeaResults').addEventListener('click', () => clearResults('idea'));
    document.getElementById('clearPitchResults').addEventListener('click', () => clearResults('pitch'));

    // Export buttons
    document.getElementById('exportIdeaResults').addEventListener('click', () => exportIdeaResults());
    document.getElementById('exportPitchResults').addEventListener('click', () => exportPitchResults());

    // Sample data buttons
    document.getElementById('loadIdeaSample').addEventListener('click', () => {
        document.getElementById('businessIdea').value = SAMPLE_IDEA_1;
        showSuccess('Sample data loaded!');
    });

    document.getElementById('loadPitchSample').addEventListener('click', () => {
        document.getElementById('pitchTranscript').value = SAMPLE_PITCH;
        showSuccess('Sample data loaded!');
    });

    // Save prompt buttons
    document.getElementById('saveIdeaPrompt').addEventListener('click', () => {
        const prompt = document.getElementById('ideaSystemPrompt').value.trim();
        if (prompt) {
            savePromptTemplate('idea', prompt);
            showSuccess('Idea evaluation prompt saved! It will be used as default.');
        } else {
            showError('Cannot save empty prompt');
        }
    });

    document.getElementById('savePitchPrompt').addEventListener('click', () => {
        const prompt = document.getElementById('pitchSystemPrompt').value.trim();
        if (prompt) {
            savePromptTemplate('pitch', prompt);
            showSuccess('Pitch evaluation prompt saved! It will be used as default.');
        } else {
            showError('Cannot save empty prompt');
        }
    });

    // Idea Generation event listeners
    document.getElementById('generateIdea').addEventListener('click', generateIdeaFromTranscript);

    document.getElementById('clearIdeaGenResults').addEventListener('click', () => clearResults('ideagen'));

    document.getElementById('exportIdeaGenResults').addEventListener('click', () => exportIdeaGenResults());

    document.getElementById('loadIdeaGenSample').addEventListener('click', () => {
        document.getElementById('ideaGenTranscript').value = SAMPLE_IDEA_GEN_TRANSCRIPT;
        showSuccess('Sample transcript loaded!');
    });

    document.getElementById('saveIdeaGenPrompt').addEventListener('click', () => {
        const prompt = document.getElementById('ideaGenSystemPrompt').value.trim();
        if (prompt) {
            savePromptTemplate('ideagen', prompt);
            showSuccess('Idea generation prompt saved! It will be used as default.');
        } else {
            showError('Cannot save empty prompt');
        }
    });

    // Idea Image Generation event listeners
    document.getElementById('generateIdeaImage').addEventListener('click', handleGenerateIdeaImage);

    document.getElementById('saveIdeaImagePrompt').addEventListener('click', () => {
        const prompt = document.getElementById('ideaImagePrompt').value.trim();
        if (prompt) {
            savePromptTemplate('ideagen-image', prompt);
            showSuccess('Image prompt template saved! It will be used as default.');
        } else {
            showError('Cannot save empty prompt');
        }
    });

    ['ideaImageModel', 'ideaImageBatchModel'].forEach(id => {
        const select = document.getElementById(id);
        if (select) {
            select.addEventListener('change', (e) => {
                setIdeaImageModel(e.target.value);
                showSuccess('Image model saved! It will be used as default.');
            });
        }
    });

    document.getElementById('downloadIdeaImageLarge').addEventListener('click', () => downloadIdeaImageVariant('large'));
    document.getElementById('downloadIdeaImageMedium').addEventListener('click', () => downloadIdeaImageVariant('medium'));
    document.getElementById('downloadIdeaImageSmall').addEventListener('click', () => downloadIdeaImageVariant('small'));
}

// API Integration Functions
async function callLLM(model, systemPrompt, userInput, temperature) {
    const modelConfig = CONFIG.models[model];
    if (!modelConfig) {
        throw new Error('Invalid model selected');
    }

    const apiKey = document.getElementById('apiKey').value || loadAPIKey();
    if (!apiKey) {
        throw new Error('Please enter API key for selected model');
    }

    // Use backend proxy to avoid CORS issues
    const proxyEndpoint = 'http://localhost:5001/api/evaluate/llm';
    
    try {
        const response = await fetch(proxyEndpoint, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                model: model,
                system_prompt: systemPrompt,
                user_input: userInput,
                temperature: parseFloat(temperature),
                api_key: apiKey
            })
        });

        if (!response.ok) {
            const errorData = await response.json().catch(() => ({}));
            throw new Error(errorData.error || `API request failed: ${response.status} ${response.statusText}`);
        }

        const data = await response.json();
        return data.content;
    } catch (error) {
        if (error.message.includes('API request failed') || error.message.includes('Network error')) {
            throw error;
        }
        // Check if backend is running
        if (error.message.includes('Failed to fetch') || error.message.includes('NetworkError')) {
            throw new Error('Cannot connect to backend server. Please make sure the Flask server is running on http://localhost:5001');
        }
        throw new Error(`Network error: ${error.message}`);
    }
}

function getHeaders(provider, apiKey) {
    const headers = {
        'Content-Type': 'application/json'
    };

    if (provider === 'openai') {
        headers['Authorization'] = `Bearer ${apiKey}`;
    } else if (provider === 'anthropic') {
        headers['x-api-key'] = apiKey;
        headers['anthropic-version'] = '2023-06-01';
    } else if (provider === 'google') {
        // Google uses query parameter, not header
    }

    return headers;
}

function formatRequestBody(provider, modelName, systemPrompt, userInput, temperature, apiKey) {
    if (provider === 'openai') {
        return {
            model: modelName,
            messages: [
                { role: 'system', content: systemPrompt },
                { role: 'user', content: userInput }
            ],
            temperature: parseFloat(temperature),
            max_tokens: CONFIG.maxTokens
        };
    } else if (provider === 'anthropic') {
        return {
            model: modelName,
            max_tokens: CONFIG.maxTokens,
            temperature: parseFloat(temperature),
            system: systemPrompt,
            messages: [
                { role: 'user', content: userInput }
            ]
        };
    } else if (provider === 'google') {
        // Google API format
        return {
            contents: [{
                parts: [{
                    text: `${systemPrompt}\n\nUser Input:\n${userInput}`
                }]
            }],
            generationConfig: {
                temperature: parseFloat(temperature),
                maxOutputTokens: CONFIG.maxTokens
            }
        };
    }
}

function extractResponseText(provider, response) {
    if (provider === 'openai') {
        return response.choices[0].message.content;
    } else if (provider === 'anthropic') {
        return response.content[0].text;
    } else if (provider === 'google') {
        return response.candidates[0].content.parts[0].text;
    }
    throw new Error('Unknown provider');
}

function parseJSONFromResponse(text) {
    // Try direct parse
    try {
        return JSON.parse(text);
    } catch (e) {
        // Extract JSON from markdown code blocks
        const jsonMatch = text.match(/```json\n?([\s\S]*?)\n?```/);
        if (jsonMatch) {
            try {
                return JSON.parse(jsonMatch[1]);
            } catch (e2) {
                // Continue to next method
            }
        }
        
        // Extract JSON object from text
        const objectMatch = text.match(/\{[\s\S]*\}/);
        if (objectMatch) {
            try {
                return JSON.parse(objectMatch[0]);
            } catch (e3) {
                // Continue to next method
            }
        }
        
        // Try extracting between ``` and ```
        const codeBlockMatch = text.match(/```\n?([\s\S]*?)\n?```/);
        if (codeBlockMatch) {
            try {
                return JSON.parse(codeBlockMatch[1]);
            } catch (e4) {
                // Last attempt failed
            }
        }
        
        throw new Error('Could not parse JSON from response');
    }
}

// Evaluation Functions
async function evaluateIdeas() {
    const businessIdea = document.getElementById('businessIdea').value.trim();
    const systemPrompt = document.getElementById('ideaSystemPrompt').value;
    const model = document.getElementById('modelSelect').value;
    const temperature = document.getElementById('temperature').value;

    // Validation
    if (!businessIdea) {
        showError('Please fill in the business idea field');
        return;
    }

    if (!systemPrompt.trim()) {
        showError('Please provide a system prompt');
        return;
    }

    // Show loading state
    const loadingElement = document.getElementById('idea-loading');
    const resultsElement = document.getElementById('idea-results');
    const evaluateButton = document.getElementById('evaluateIdeas');

    loadingElement.classList.remove('hidden');
    resultsElement.classList.add('hidden');
    evaluateButton.disabled = true;

    try {
        const userInput = `BUSINESS IDEA:\n${businessIdea}`;
        const response = await callLLM(model, systemPrompt, userInput, temperature);
        const result = parseJSONFromResponse(response);

        // Display results
        displayIdeaResults(result);

        showSuccess('Idea evaluated successfully!');
    } catch (error) {
        showError(error.message || 'Failed to evaluate idea. Please try again.');
        console.error('Evaluation error:', error);
    } finally {
        loadingElement.classList.add('hidden');
        evaluateButton.disabled = false;
    }
}

async function evaluatePitch() {
    const transcript = document.getElementById('pitchTranscript').value.trim();
    const systemPrompt = document.getElementById('pitchSystemPrompt').value;
    const model = document.getElementById('modelSelect').value;
    const temperature = document.getElementById('temperature').value;

    // Validation
    if (!transcript) {
        showError('Please enter a pitch transcript');
        return;
    }

    if (!systemPrompt.trim()) {
        showError('Please provide a system prompt');
        return;
    }

    // Show loading state
    const loadingElement = document.getElementById('pitch-loading');
    const resultsElement = document.getElementById('pitch-results');
    const evaluateButton = document.getElementById('evaluatePitch');

    loadingElement.classList.remove('hidden');
    resultsElement.classList.add('hidden');
    evaluateButton.disabled = true;

    try {
        const response = await callLLM(model, systemPrompt, transcript, temperature);
        const result = parseJSONFromResponse(response);

        // Display results
        displayPitchResults(result);

        showSuccess('Pitch evaluated successfully!');
    } catch (error) {
        showError(error.message || 'Failed to evaluate pitch. Please try again.');
        console.error('Evaluation error:', error);
    } finally {
        loadingElement.classList.add('hidden');
        evaluateButton.disabled = false;
    }
}

// UI Display Functions
function displayIdeaResults(data) {
    const resultsContent = document.getElementById('idea-results-content');

    // Debug: log the data structure
    console.log('Displaying idea results:', data);
    console.log('Data keys:', Object.keys(data || {}));
    console.log('Legibility:', data?.legibility);
    console.log('Specificity:', data?.specificity);
    console.log('Executability:', data?.executability);
    console.log('Novelty:', data?.novelty);

    let html = '';
    
    // Sector badge at the top
    if (data?.sector) {
        html += `<div class="sector-badge">${escapeHtml(data.sector)}</div>`;
    }

    // Helper function to safely get nested data with key mapping
    const getNestedDataWithMapping = (obj, sectionName, label) => {
        if (!obj || !obj[sectionName]) return undefined;
        
        const section = obj[sectionName];
        const labelLower = label.toLowerCase();
        const possibleKeys = LABEL_TO_API_KEY[labelLower] || [labelLower];
        
        // Try each possible key
        for (const possibleKey of possibleKeys) {
            if (possibleKey in section) {
                return section[possibleKey];
            }
            // Try case-insensitive
            for (const key in section) {
                if (key.toLowerCase() === possibleKey.toLowerCase()) {
                    return section[key];
                }
            }
        }
        
        // Fallback to direct access
        return section[labelLower] || section[label];
    };

    // Legibility section
    html += '<div class="evaluation-section">';
    html += '<h3>Legibility</h3>';
    const clarityData = getNestedDataWithMapping(data, 'legibility', 'clarity') || data?.legibility?.is_clear || data?.legibility?.clarity;
    const coherenceData = getNestedDataWithMapping(data, 'legibility', 'coherence') || data?.legibility?.is_coherent || data?.legibility?.coherence;
    console.log('Clarity data:', clarityData, 'Type:', typeof clarityData, 'Full legibility:', data?.legibility);
    console.log('Coherence data:', coherenceData, 'Type:', typeof coherenceData);
    html += createTrueFalseIndicator('Clarity', clarityData, data?.legibility);
    html += createTrueFalseIndicator('Coherence', coherenceData, data?.legibility);
    html += '</div>';

    // Specificity section
    html += '<div class="evaluation-section">';
    html += '<h3>Specificity</h3>';
    const detailedData = getNestedDataWithMapping(data, 'specificity', 'detailed') || data?.specificity?.is_detailed_enough || data?.specificity?.is_detailed || data?.specificity?.detailed;
    const concreteData = getNestedDataWithMapping(data, 'specificity', 'concrete') || data?.specificity?.is_clearly_defined || data?.specificity?.is_concrete || data?.specificity?.concrete;
    console.log('Detailed data:', detailedData, 'Type:', typeof detailedData, 'Full specificity:', data?.specificity);
    console.log('Concrete data:', concreteData, 'Type:', typeof concreteData);
    html += createTrueFalseIndicator('Detailed', detailedData, data?.specificity);
    html += createTrueFalseIndicator('Concrete', concreteData, data?.specificity);
    if (data?.specificity?.score !== undefined) {
        html += createScoreGauge(data.specificity.score);
    }
    html += '</div>';

    // Executability section
    html += '<div class="evaluation-section">';
    html += '<h3>Executability</h3>';
    const feasibleData = getNestedDataWithMapping(data, 'executability', 'feasible') || data?.executability?.is_feasible || data?.executability?.feasible;
    const actionableData = getNestedDataWithMapping(data, 'executability', 'actionable') || data?.executability?.is_actionable || data?.executability?.actionable;
    console.log('Feasible data:', feasibleData, 'Type:', typeof feasibleData, 'Full executability:', data?.executability);
    console.log('Actionable data:', actionableData, 'Type:', typeof actionableData);
    html += createTrueFalseIndicator('Feasible', feasibleData, data?.executability);
    html += createTrueFalseIndicator('Actionable', actionableData, data?.executability);
    html += '</div>';

    // Novelty section
    html += '<div class="evaluation-section">';
    html += '<h3>Novelty</h3>';
    const novelData = getNestedDataWithMapping(data, 'novelty', 'novel') || data?.novelty?.is_novel || data?.novelty?.novel;
    console.log('Novel data:', novelData, 'Type:', typeof novelData, 'Full novelty:', data?.novelty);
    html += createTrueFalseIndicator('Novel', novelData, data?.novelty);
    html += '</div>';

    // Always show debug info to help diagnose the issue
    html += '<div class="evaluation-section" style="background: rgba(245, 158, 11, 0.1); border: 2px solid var(--warning);">';
    html += '<h3>🔍 Debug: Received Data Structure</h3>';
    html += `<pre style="color: var(--text-light); white-space: pre-wrap; font-size: 0.85rem; max-height: 400px; overflow-y: auto;">${escapeHtml(JSON.stringify(data, null, 2))}</pre>`;
    html += '<h4 style="margin-top: 20px; color: var(--warning);">Data Access Attempts:</h4>';
    html += `<ul style="color: var(--text-light); font-size: 0.9rem;">`;
    html += `<li>legibility.clarity: ${data?.legibility?.clarity !== undefined ? JSON.stringify(data.legibility.clarity) : 'undefined'}</li>`;
    html += `<li>legibility.coherence: ${data?.legibility?.coherence !== undefined ? JSON.stringify(data.legibility.coherence) : 'undefined'}</li>`;
    html += `<li>specificity.detailed: ${data?.specificity?.detailed !== undefined ? JSON.stringify(data.specificity.detailed) : 'undefined'}</li>`;
    html += `<li>specificity.concrete: ${data?.specificity?.concrete !== undefined ? JSON.stringify(data.specificity.concrete) : 'undefined'}</li>`;
    html += `<li>executability.feasible: ${data?.executability?.feasible !== undefined ? JSON.stringify(data.executability.feasible) : 'undefined'}</li>`;
    html += `<li>executability.actionable: ${data?.executability?.actionable !== undefined ? JSON.stringify(data.executability.actionable) : 'undefined'}</li>`;
    html += `<li>novelty.novel: ${data?.novelty?.novel !== undefined ? JSON.stringify(data.novelty.novel) : 'undefined'}</li>`;
    html += '</ul>';
    html += '</div>';

    resultsContent.innerHTML = html;
    document.getElementById('idea-results').classList.remove('hidden');
    resultsContent.dataset.currentResults = JSON.stringify(data);
}

// Mapping from UI labels to possible API key names
const LABEL_TO_API_KEY = {
    'clarity': ['is_clear', 'clarity', 'is_clarity', 'clear'],
    'coherence': ['is_coherent', 'coherence', 'is_coherence', 'coherent'],
    'detailed': ['is_detailed_enough', 'is_detailed', 'detailed', 'is_detail', 'detail'],
    'concrete': ['is_clearly_defined', 'is_concrete', 'concrete', 'clearly_defined'],
    'feasible': ['is_feasible', 'feasible', 'feasibility'],
    'actionable': ['is_actionable', 'actionable', 'actionability'],
    'novel': ['is_novel', 'novel', 'novelty', 'is_novelty']
};

function extractValueFromSection(section, label) {
    if (!section || typeof section !== 'object') return null;
    
    const labelLower = label.toLowerCase();
    
    // Get possible API keys for this label
    const possibleKeys = LABEL_TO_API_KEY[labelLower] || [labelLower];
    
    // Try each possible key
    for (const possibleKey of possibleKeys) {
        // Try exact match
        if (possibleKey in section) {
            return section[possibleKey];
        }
        // Try case-insensitive match
        for (const key in section) {
            if (key.toLowerCase() === possibleKey.toLowerCase()) {
                return section[key];
            }
        }
    }
    
    // Try partial match with any key
    for (const key in section) {
        const keyLower = key.toLowerCase();
        if (keyLower.includes(labelLower) || labelLower.includes(keyLower)) {
            return section[key];
        }
    }
    
    // Recursively search nested objects
    for (const key in section) {
        if (typeof section[key] === 'object' && section[key] !== null) {
            const found = extractValueFromSection(section[key], label);
            if (found !== null) return found;
        }
    }
    
    return null;
}

function createTrueFalseIndicator(label, data, parentSection = null) {
    console.log(`Creating indicator for "${label}":`, data, 'Type:', typeof data, 'Parent:', parentSection);
    
    let value, reason;
    
    // Handle different data structures
    if (data === null || data === undefined) {
        // Try to find the value in the parent section using the label as a key
        if (parentSection && typeof parentSection === 'object') {
            const foundData = extractValueFromSection(parentSection, label);
            if (foundData !== null && foundData !== undefined) {
                console.log(`${label}: Found in parent section:`, foundData);
                return createTrueFalseIndicator(label, foundData, null);
            }
            // Also try searching all keys in parent section with label mapping
            console.log(`${label}: Searching parent section keys:`, Object.keys(parentSection));
            const labelLower = label.toLowerCase();
            const possibleKeys = LABEL_TO_API_KEY[labelLower] || [labelLower];
            
            for (const possibleKey of possibleKeys) {
                for (const key in parentSection) {
                    const keyLower = key.toLowerCase();
                    if (keyLower === possibleKey.toLowerCase() || 
                        keyLower.includes(possibleKey.toLowerCase()) || 
                        possibleKey.toLowerCase().includes(keyLower)) {
                        const foundData = parentSection[key];
                        console.log(`${label}: Found matching key "${key}" (looking for "${possibleKey}"):`, foundData);
                        return createTrueFalseIndicator(label, foundData, null);
                    }
                }
            }
        }
        value = false;
        reason = `No data provided for ${label}. Available keys in parent: ${parentSection ? Object.keys(parentSection).join(', ') : 'none'}`;
        console.warn(`No data for ${label}, parent keys:`, parentSection ? Object.keys(parentSection) : 'no parent');
    } else if (typeof data === 'boolean') {
        value = data;
        reason = 'No reason provided';
        console.log(`${label}: Direct boolean value = ${value}`);
    } else if (typeof data === 'object' && data !== null) {
        console.log(`${label}: Processing object:`, Object.keys(data));
        
        // Check for value property (expected structure: {value: true/false, reason: "..."})
        if ('value' in data) {
            value = data.value;
            // Try multiple possible field names for reason
            reason = data.reason || data.justification || data.explanation || data.rationale || data.comment || data.note || '';
            if (!reason || reason.trim() === '') {
                reason = 'No reason provided';
            }
            console.log(`${label}: Found value property = ${value}, reason length = ${reason.length}`);
        } 
        // Check if the object has a direct boolean property
        else if (label.toLowerCase() in data && typeof data[label.toLowerCase()] === 'boolean') {
            value = data[label.toLowerCase()];
            reason = data.reason || data.justification || data[label.toLowerCase() + '_reason'] || 'No reason provided';
            console.log(`${label}: Found boolean property = ${value}`);
        }
        // Try to find any boolean value in the object
        else {
            const boolKeys = Object.keys(data).filter(key => typeof data[key] === 'boolean');
            if (boolKeys.length > 0) {
                value = data[boolKeys[0]];
                reason = data.reason || data.justification || data[boolKeys[0] + '_reason'] || 'No reason provided';
                console.log(`${label}: Found boolean in keys: ${boolKeys[0]} = ${value}`);
            } else {
                // If no boolean found, check for string values that might be "true"/"false"
                const stringKeys = Object.keys(data).filter(key => 
                    typeof data[key] === 'string' && (data[key].toLowerCase() === 'true' || data[key].toLowerCase() === 'false')
                );
                if (stringKeys.length > 0) {
                    value = data[stringKeys[0]].toLowerCase() === 'true';
                    reason = data.reason || data.justification || 'No reason provided';
                    console.log(`${label}: Found string boolean: ${stringKeys[0]} = ${value}`);
                } else {
                    // Check all keys for nested objects with 'value' property
                    const allKeys = Object.keys(data);
                    let found = false;
                    for (const key of allKeys) {
                        if (typeof data[key] === 'object' && data[key] !== null && 'value' in data[key]) {
                            value = data[key].value;
                            reason = data[key].reason || data[key].justification || data[key].explanation || data[key].rationale || '';
                            if (!reason || reason.trim() === '') {
                                reason = 'No reason provided';
                            }
                            console.log(`${label}: Found nested value in ${key} = ${value}, reason length = ${reason.length}`);
                            found = true;
                            break;
                        }
                    }
                    if (!found) {
                        // Last resort: show the raw data structure
                        value = false;
                        reason = `Data structure: ${JSON.stringify(data)}`;
                        console.warn(`${label}: Could not parse structure:`, data);
                    }
                }
            }
        }
    } else if (typeof data === 'string') {
        // Try to parse string as boolean
        value = data.toLowerCase() === 'true' || data === '1';
        reason = 'No reason provided';
        console.log(`${label}: String value = ${value}`);
    } else if (typeof data === 'number') {
        // Treat 1 as true, 0 as false
        value = data === 1;
        reason = 'No reason provided';
        console.log(`${label}: Number value = ${value}`);
    } else {
        // Try to parse as boolean
        value = data === true || data === 1;
        reason = 'No reason provided';
        console.log(`${label}: Other type, parsed as = ${value}`);
    }
    
    const isTrue = value === true || value === 'true' || value === 'True' || value === 1;
    const colorClass = isTrue ? 'indicator-true' : 'indicator-false';
    const icon = isTrue ? '✓' : '✗';
    
    console.log(`${label}: Final value = ${isTrue} (${value})`);
    
    return `
        <div class="true-false-indicator">
            <div class="indicator-header">
                <span class="indicator-label">${escapeHtml(label)}</span>
                <span class="indicator-value ${colorClass}">
                    <span class="indicator-icon">${icon}</span>
                    <span class="indicator-text">${isTrue ? 'True' : 'False'}</span>
                </span>
            </div>
            <div class="indicator-reason">${escapeHtml(reason)}</div>
        </div>
    `;
}

function createScoreGauge(score, label = 'Score') {
    const percentage = Math.min(100, Math.max(0, (score / 10) * 100));
    let scoreClass = 'score-low';
    
    if (score >= 7) {
        scoreClass = 'score-high';
    } else if (score >= 5) {
        scoreClass = 'score-medium';
    }
    
    return `
        <div class="score-gauge-container">
            <div class="score-gauge-label">${escapeHtml(label)}: ${score}/10</div>
            <div class="score-gauge">
                <div class="score-gauge-fill ${scoreClass}" style="width: ${percentage}%"></div>
            </div>
        </div>
    `;
}

function displayPitchResults(data) {
    const resultsContent = document.getElementById('pitch-results-content');

    // Debug: log the data structure
    console.log('Displaying pitch results:', data);

    let html = '';

    // Sector badge at the top
    if (data?.sector) {
        html += `<div class="sector-badge">${escapeHtml(data.sector)}</div>`;
    }

    // Articulation Section
    if (data.articulation) {
        html += '<div class="evaluation-section">';
        html += '<h3>Articulation of Business Idea & Problem</h3>';
        
        // Is idea clearly defined
        html += createTrueFalseIndicator('Business Idea Clarity', data.articulation.is_idea_clearly_defined);
        
        // Is problem or need mentioned
        html += createTrueFalseIndicator('Problem/Need Mentioned', data.articulation.is_problem_or_need_mentioned);
        
        // Articulation score
        if (data.articulation.score !== undefined) {
            html += createScoreGauge(data.articulation.score, 'Articulation Score');
        }
        
        html += '</div>';
    }

    // Product/Service Description Section
    if (data.product_service_description) {
        html += '<div class="evaluation-section">';
        html += '<h3>Product/Service Description</h3>';
        
        // Is USP mentioned
        html += createTrueFalseIndicator('USP Mentioned', data.product_service_description.is_usp_mentioned);
        
        // Is selling plan or target customers mentioned
        html += createTrueFalseIndicator('Selling Plan/Target Customers', data.product_service_description.is_selling_plan_or_target_customers_mentioned);
        
        // Quality score
        if (data.product_service_description.quality_score !== undefined) {
            html += createScoreGauge(data.product_service_description.quality_score, 'Quality Score');
        }
        
        html += '</div>';
    }

    // Transcript Quality Note (if present)
    if (data.transcript_quality_note && data.transcript_quality_note.trim()) {
        html += '<div class="evaluation-section transcript-note">';
        html += '<h3>Transcript Quality Note</h3>';
        html += `<p class="transcript-quality-text">${escapeHtml(data.transcript_quality_note)}</p>`;
        html += '</div>';
    }

    // Summary Section with overall scores
    html += '<div class="evaluation-section summary-section">';
    html += '<h3>Summary</h3>';
    html += '<div class="summary-grid">';
    
    // Boolean indicators summary
    const booleanResults = [];
    if (data.articulation?.is_idea_clearly_defined?.value !== undefined) {
        booleanResults.push({ label: 'Idea Clear', value: data.articulation.is_idea_clearly_defined.value });
    }
    if (data.articulation?.is_problem_or_need_mentioned?.value !== undefined) {
        booleanResults.push({ label: 'Problem/Need', value: data.articulation.is_problem_or_need_mentioned.value });
    }
    if (data.product_service_description?.is_usp_mentioned?.value !== undefined) {
        booleanResults.push({ label: 'USP', value: data.product_service_description.is_usp_mentioned.value });
    }
    if (data.product_service_description?.is_selling_plan_or_target_customers_mentioned?.value !== undefined) {
        booleanResults.push({ label: 'Selling Plan', value: data.product_service_description.is_selling_plan_or_target_customers_mentioned.value });
    }

    if (booleanResults.length > 0) {
        html += '<div class="boolean-summary">';
        booleanResults.forEach(item => {
            const icon = item.value ? '✓' : '✗';
            const colorClass = item.value ? 'indicator-true' : 'indicator-false';
            html += `<span class="summary-badge ${colorClass}">${icon} ${escapeHtml(item.label)}</span>`;
        });
        html += '</div>';
    }

    // Scores summary
    const scores = [];
    if (data.articulation?.score !== undefined) {
        scores.push({ label: 'Articulation', score: data.articulation.score });
    }
    if (data.product_service_description?.quality_score !== undefined) {
        scores.push({ label: 'Quality', score: data.product_service_description.quality_score });
    }

    if (scores.length > 0) {
        html += '<div class="scores-summary">';
        scores.forEach(item => {
            let scoreClass = 'score-low';
            if (item.score >= 7) scoreClass = 'score-high';
            else if (item.score >= 5) scoreClass = 'score-medium';
            html += `<div class="score-badge ${scoreClass}"><span class="score-label">${escapeHtml(item.label)}:</span> <span class="score-value">${item.score}/10</span></div>`;
        });
        html += '</div>';
    }

    html += '</div>';
    html += '</div>';

    // Debug section (can be removed in production)
    html += '<div class="evaluation-section" style="background: rgba(59, 130, 246, 0.1); border: 2px solid var(--primary);">';
    html += '<h3>Raw Evaluation Data</h3>';
    html += `<pre style="color: var(--text-light); white-space: pre-wrap; font-size: 0.85rem; max-height: 300px; overflow-y: auto;">${escapeHtml(JSON.stringify(data, null, 2))}</pre>`;
    html += '</div>';

    resultsContent.innerHTML = html;
    document.getElementById('pitch-results').classList.remove('hidden');
    resultsContent.dataset.currentResults = JSON.stringify(data);
}

function createScoreDisplay(label, scoreData) {
    if (!scoreData || typeof scoreData.score === 'undefined') {
        return '';
    }
    
    const score = scoreData.score;
    const justification = scoreData.justification || 'No justification provided';
    let scoreClass = 'score-low';
    
    if (score >= 8) {
        scoreClass = 'score-high';
    } else if (score >= 5) {
        scoreClass = 'score-medium';
    }

    return `
        <div class="score-item">
            <div class="score-label">${escapeHtml(label)}</div>
            <div class="score-value ${scoreClass}">${score}</div>
            <div class="score-justification">${escapeHtml(justification)}</div>
        </div>
    `;
}

function createPitchScoreCard(label, scoreData) {
    if (!scoreData || typeof scoreData.score === 'undefined') {
        return '';
    }

    const score = scoreData.score;
    const justification = scoreData.justification || 'No justification provided';
    const strengths = scoreData.strengths || 'No strengths identified';
    const improvements = scoreData.improvements || 'No improvements suggested';
    
    let scoreClass = 'score-low';
    if (score >= 8) {
        scoreClass = 'score-high';
    } else if (score >= 5) {
        scoreClass = 'score-medium';
    }

    return `
        <div class="pitch-card">
            <h3>${escapeHtml(label)}</h3>
            <div class="score-value ${scoreClass}">${score}</div>
            <div class="score-label">Justification</div>
            <div class="score-justification">${escapeHtml(justification)}</div>
            <div class="strengths">
                <h4>Strengths</h4>
                <p>${escapeHtml(strengths)}</p>
            </div>
            <div class="improvements">
                <h4>Improvements</h4>
                <p>${escapeHtml(improvements)}</p>
            </div>
        </div>
    `;
}

// Idea Generation Functions
async function generateIdeaFromTranscript() {
    const transcript = document.getElementById('ideaGenTranscript').value.trim();
    const systemPrompt = document.getElementById('ideaGenSystemPrompt').value;
    const model = document.getElementById('modelSelect').value;
    const temperature = document.getElementById('temperature').value;

    if (!transcript) {
        showError('Please enter a pitch transcript');
        return;
    }

    if (!systemPrompt.trim()) {
        showError('Please provide a system prompt');
        return;
    }

    const loadingElement = document.getElementById('ideagen-loading');
    const resultsElement = document.getElementById('ideagen-results');
    const evaluateButton = document.getElementById('generateIdea');

    loadingElement.classList.remove('hidden');
    resultsElement.classList.add('hidden');
    evaluateButton.disabled = true;
    resetIdeaImageUI();

    try {
        const userInput = `Transcript:\n${transcript}`;
        const response = await callLLM(model, systemPrompt, userInput, temperature);
        const result = parseJSONFromResponse(response);

        if (result.status === 'unprocessable') {
            showError(`Unprocessable: ${result.reason}`);
            return;
        }

        displayIdeaGenResults(result);
        showSuccess('Idea generated successfully!');
    } catch (error) {
        showError(error.message || 'Failed to generate idea. Please try again.');
        console.error('Idea generation error:', error);
    } finally {
        loadingElement.classList.add('hidden');
        evaluateButton.disabled = false;
    }
}

function displayIdeaGenResults(data) {
    const resultsContent = document.getElementById('ideagen-results-content');
    let html = '';

    // Idea Title as hero
    if (data.idea_title) {
        html += `<div class="ideagen-title-card">
            <span class="ideagen-title-label">Idea Title</span>
            <h2 class="ideagen-title-text">${escapeHtml(data.idea_title)}</h2>
        </div>`;
    }

    // Problem / Opportunity
    if (data.problem_or_opportunity) {
        html += `<div class="ideagen-field-card ideagen-problem-card">
            <div class="ideagen-field-icon">&#x1F50D;</div>
            <div class="ideagen-field-body">
                <span class="ideagen-field-label">Problem or Opportunity</span>
                <p class="ideagen-field-value">${escapeHtml(data.problem_or_opportunity)}</p>
            </div>
        </div>`;
    }

    // Tags row: themes + categories
    html += '<div class="ideagen-tags-row">';

    if (data.problem_opportunity_themes && data.problem_opportunity_themes.length > 0) {
        html += '<div class="ideagen-tag-group">';
        html += '<span class="ideagen-tag-group-label">Problem Themes</span>';
        html += '<div class="ideagen-tag-list">';
        data.problem_opportunity_themes.forEach(theme => {
            html += `<span class="ideagen-tag ideagen-tag-theme">${escapeHtml(theme)}</span>`;
        });
        html += '</div></div>';
    }

    if (data.business_categories && data.business_categories.length > 0) {
        html += '<div class="ideagen-tag-group">';
        html += '<span class="ideagen-tag-group-label">Business Categories</span>';
        html += '<div class="ideagen-tag-list">';
        data.business_categories.forEach(cat => {
            html += `<span class="ideagen-tag ideagen-tag-category">${escapeHtml(cat)}</span>`;
        });
        html += '</div></div>';
    }

    if (data.business_subcategories && data.business_subcategories.length > 0) {
        html += '<div class="ideagen-tag-group">';
        html += '<span class="ideagen-tag-group-label">Business Subcategories</span>';
        html += '<div class="ideagen-tag-list">';
        data.business_subcategories.forEach(subcat => {
            html += `<span class="ideagen-tag ideagen-tag-category">${escapeHtml(subcat)}</span>`;
        });
        html += '</div></div>';
    }

    html += '</div>';

    // Solution Details
    if (data.solution_details) {
        html += `<div class="ideagen-field-card ideagen-solution-card">
            <div class="ideagen-field-icon">&#x1F4A1;</div>
            <div class="ideagen-field-body">
                <span class="ideagen-field-label">Solution Details</span>
                <p class="ideagen-field-value">${escapeHtml(data.solution_details)}</p>
            </div>
        </div>`;
    }

    // Potential Impact
    if (data.potential_impact) {
        html += `<div class="ideagen-field-card ideagen-impact-card">
            <div class="ideagen-field-icon">&#x1F31F;</div>
            <div class="ideagen-field-body">
                <span class="ideagen-field-label">Potential Impact</span>
                <p class="ideagen-field-value">${escapeHtml(data.potential_impact)}</p>
            </div>
        </div>`;
    }

    // Raw JSON accordion
    html += `<details class="ideagen-raw-details">
        <summary>View Raw JSON</summary>
        <pre class="ideagen-raw-json">${escapeHtml(JSON.stringify(data, null, 2))}</pre>
    </details>`;

    resultsContent.innerHTML = html;
    document.getElementById('ideagen-results').classList.remove('hidden');
    resultsContent.dataset.currentResults = JSON.stringify(data);

    // Reveal the representative-image section now that text results exist.
    document.getElementById('ideagen-image-section').classList.remove('hidden');
}

function exportIdeaGenResults() {
    const resultsContent = document.getElementById('ideagen-results-content');
    const currentResults = resultsContent.dataset.currentResults;

    if (!currentResults) {
        showError('No results to export');
        return;
    }

    try {
        const data = JSON.parse(currentResults);

        // Merge image data if a representative image has been generated.
        const imageState = ideaImageState;
        if (imageState && imageState.variants) {
            data.image_prompt = imageState.prompt;
            data.image_variants = {
                '197x171': `data:image/png;base64,${imageState.variants.large}`,
                '156x171': `data:image/png;base64,${imageState.variants.medium}`,
                '116x171': `data:image/png;base64,${imageState.variants.small}`
            };
        }

        const filename = `idea-generation-${new Date().toISOString().split('T')[0]}.json`;
        downloadFile(JSON.stringify(data, null, 2), filename, 'application/json');
        showSuccess('Results exported successfully!');
    } catch (error) {
        showError('Failed to export results');
    }
}

// Holds the latest generated image bundle for the single-idea flow.
// Shape: { prompt: string, variants: { large, medium, small } } | null
let ideaImageState = null;

function resetIdeaImageUI() {
    ideaImageState = null;
    const resultsBlock = document.getElementById('ideagen-image-results');
    if (resultsBlock) resultsBlock.classList.add('hidden');

    ['ideagen-image-large', 'ideagen-image-medium', 'ideagen-image-small'].forEach(id => {
        const img = document.getElementById(id);
        if (img) img.removeAttribute('src');
    });

    const resolvedEl = document.getElementById('ideagen-image-resolved-prompt');
    if (resolvedEl) resolvedEl.textContent = '';

    const loadingEl = document.getElementById('ideagen-image-loading');
    if (loadingEl) loadingEl.classList.add('hidden');
}

async function handleGenerateIdeaImage() {
    const resultsContent = document.getElementById('ideagen-results-content');
    const currentResults = resultsContent.dataset.currentResults;
    if (!currentResults) {
        showError('Generate an idea first before generating an image.');
        return;
    }

    const template = document.getElementById('ideaImagePrompt').value;
    if (!template.trim()) {
        showError('Please provide an image prompt template.');
        return;
    }

    const model = document.getElementById('ideaImageModel')?.value || loadImageModel();

    const apiKey = document.getElementById('apiKey').value || loadAPIKey();
    if (!apiKey) {
        showError('Please enter an OpenAI API key.');
        return;
    }

    let ideaData;
    try {
        ideaData = JSON.parse(currentResults);
    } catch (err) {
        showError('Could not read the current idea data.');
        return;
    }

    const button = document.getElementById('generateIdeaImage');
    const loadingEl = document.getElementById('ideagen-image-loading');
    const resultsBlock = document.getElementById('ideagen-image-results');

    button.disabled = true;
    loadingEl.classList.remove('hidden');
    resultsBlock.classList.add('hidden');

    try {
        const bundle = await generateIdeaImageBundle(ideaData, template, apiKey, model);

        document.getElementById('ideagen-image-large').src  = `data:image/png;base64,${bundle.variants.large}`;
        document.getElementById('ideagen-image-medium').src = `data:image/png;base64,${bundle.variants.medium}`;
        document.getElementById('ideagen-image-small').src  = `data:image/png;base64,${bundle.variants.small}`;
        document.getElementById('ideagen-image-resolved-prompt').textContent = bundle.prompt;

        ideaImageState = { prompt: bundle.prompt, variants: bundle.variants };
        resultsBlock.classList.remove('hidden');
        showSuccess('Image generated successfully!');
    } catch (error) {
        showError(error.message || 'Failed to generate image.');
        console.error('Image generation error:', error);
    } finally {
        loadingEl.classList.add('hidden');
        button.disabled = false;
    }
}

function downloadIdeaImageVariant(variantKey) {
    if (!ideaImageState || !ideaImageState.variants || !ideaImageState.variants[variantKey]) {
        showError('No image to download. Generate one first.');
        return;
    }
    const variantDef = IDEA_IMAGE_VARIANTS.find(v => v.key === variantKey);
    const sizeLabel = variantDef ? `${variantDef.width}x${variantDef.height}` : variantKey;
    const a = document.createElement('a');
    a.href = `data:image/png;base64,${ideaImageState.variants[variantKey]}`;
    a.download = `idea-image-${sizeLabel}.png`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
}

function clearResults(evaluationType) {
    if (evaluationType === 'idea') {
        document.getElementById('idea-results').classList.add('hidden');
        document.getElementById('idea-results-content').innerHTML = '';
        document.getElementById('idea-results-content').removeAttribute('data-current-results');
    } else if (evaluationType === 'pitch') {
        document.getElementById('pitch-results').classList.add('hidden');
        document.getElementById('pitch-results-content').innerHTML = '';
        document.getElementById('pitch-results-content').removeAttribute('data-current-results');
    } else if (evaluationType === 'ideagen') {
        document.getElementById('ideagen-results').classList.add('hidden');
        document.getElementById('ideagen-results-content').innerHTML = '';
        document.getElementById('ideagen-results-content').removeAttribute('data-current-results');
        resetIdeaImageUI();
        document.getElementById('ideagen-image-section').classList.add('hidden');
    }
}

function togglePromptSection(sectionId) {
    const section = document.getElementById(sectionId);
    const button = section.previousElementSibling;
    const icon = button.querySelector('.collapse-icon');

    section.classList.toggle('collapsed');
    
    if (section.classList.contains('collapsed')) {
        icon.textContent = '▶';
    } else {
        icon.textContent = '▼';
    }
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Message Functions
function showError(message) {
    const errorElement = document.getElementById('error-message');
    errorElement.textContent = message;
    errorElement.classList.remove('hidden');
    
    setTimeout(() => {
        errorElement.classList.add('hidden');
    }, 5000);
}

function showSuccess(message) {
    const successElement = document.getElementById('success-message');
    successElement.textContent = message;
    successElement.classList.remove('hidden');
    
    setTimeout(() => {
        successElement.classList.add('hidden');
    }, 3000);
}

// Local Storage Functions
function saveAPIKey(key) {
    const model = document.getElementById('modelSelect').value;
    localStorage.setItem(`apiKey_${model}`, key);
}

function loadAPIKey() {
    const model = document.getElementById('modelSelect').value;
    const key = localStorage.getItem(`apiKey_${model}`);
    if (key) {
        document.getElementById('apiKey').value = key;
    }
    return key || '';
}

function savePromptTemplate(type, prompt) {
    localStorage.setItem(`prompt_${type}`, prompt);
}

function loadPromptTemplate(type) {
    return localStorage.getItem(`prompt_${type}`) || null;
}

function saveImageModel(model) {
    localStorage.setItem('prompt_ideagen-image-model', model);
}

function loadImageModel() {
    return localStorage.getItem('prompt_ideagen-image-model') || DEFAULT_IDEA_IMAGE_MODEL;
}

function setIdeaImageModel(model) {
    const selected = IDEA_IMAGE_MODEL_OPTIONS.some(opt => opt.value === model) ? model : DEFAULT_IDEA_IMAGE_MODEL;
    ['ideaImageModel', 'ideaImageBatchModel'].forEach(id => {
        const select = document.getElementById(id);
        if (select) select.value = selected;
    });
    saveImageModel(selected);
}

function loadSavedData() {
    // Load API key for current model
    loadAPIKey();

    // Update API key when model changes
    document.getElementById('modelSelect').addEventListener('change', () => {
        loadAPIKey();
    });
}

// Export Functions
function exportIdeaResults() {
    const resultsContent = document.getElementById('idea-results-content');
    const currentResults = resultsContent.dataset.currentResults;
    
    if (!currentResults) {
        showError('No results to export');
        return;
    }

    try {
        const data = JSON.parse(currentResults);
        const filename = `idea-evaluation-${new Date().toISOString().split('T')[0]}.json`;
        downloadFile(JSON.stringify(data, null, 2), filename, 'application/json');
        showSuccess('Results exported successfully!');
    } catch (error) {
        showError('Failed to export results');
    }
}

function exportPitchResults() {
    const resultsContent = document.getElementById('pitch-results-content');
    const currentResults = resultsContent.dataset.currentResults;
    
    if (!currentResults) {
        showError('No results to export');
        return;
    }

    try {
        const data = JSON.parse(currentResults);
        const filename = `pitch-evaluation-${new Date().toISOString().split('T')[0]}.json`;
        downloadFile(JSON.stringify(data, null, 2), filename, 'application/json');
        showSuccess('Results exported successfully!');
    } catch (error) {
        showError('Failed to export results');
    }
}

function downloadFile(content, filename, type) {
    const blob = new Blob([content], { type: type });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
}
