# Future Chapter: Research Notes

Notes toward a new chapter built from section <!--ref:r105-->[§1.7](https://github.com/simbrain/NeuralNetworksCogSciBook/blob/1371c5da040ff388fde37e438f47b625a71e13f8/Transformers.tex#L1270)<!--/ref--> of `Transformers.tex` ("LLMs in Practice") and parts of `AI_Alignment.tex`.

## Possible titles

- From Model to Mind
- LLMs in Practice
- LLMs as Cognitive Systems
- Beyond the Base Model
- From Model to Mind: Fine-Tuning, Prompts, and Agents

## Line-by-line suggestions

**<!--ref:r067-->[Line 1272](https://github.com/simbrain/NeuralNetworksCogSciBook/blob/1371c5da040ff388fde37e438f47b625a71e13f8/Transformers.tex#L1272)<!--/ref--> (split plan)** <!--ref:r068-->[§1.7 LLMs in Practice](https://github.com/simbrain/NeuralNetworksCogSciBook/blob/1371c5da040ff388fde37e438f47b625a71e13f8/Transformers.tex#L1270)<!--/ref-->: I noticed that some sections were slightly redundant in explaining fine-tuning and base models, so the plan to separate that material from the transformers chapter and combine some of it with the AI alignment chapter makes sense to me.

**<!--ref:r069-->[Lines 1274-1276](https://github.com/simbrain/NeuralNetworksCogSciBook/blob/1371c5da040ff388fde37e438f47b625a71e13f8/Transformers.tex#L1274-L1276)<!--/ref--> (role tokens/harness)** <!--ref:r070-->[§1.7 LLMs in Practice](https://github.com/simbrain/NeuralNetworksCogSciBook/blob/1371c5da040ff388fde37e438f47b625a71e13f8/Transformers.tex#L1270)<!--/ref-->: I used to spend a lot of time tweaking [SillyTavern](https://docs.sillytavern.app/), an open-source frontend that makes it easier to use LLMs for building detailed custom role-play chatbots. I think it could count as an example of a harness too. I'm familiar with how role markers are used to keep the system instructions, the user's messages, and the model's replies separate. Three years ago, models would sometimes mix up the roles and start writing the user's side of the role-play, especially if the template didn't match the model or the model was weaker. That's similar to what section 4.2 says about base models continuing to simulate the human user. When I recently tried it again for this project, I found that it doesn't happen anymore (at least in the chats I tested). Likely reasons include stronger chat tuning and models using their own native role tokens rather than improvised templates; I could look into this further later.

A possible cognitive science link is source monitoring: the model loses track of which lines are its own and which belong to someone else, which is a kind of self-other misattribution.

**<!--ref:r071-->[Line 1278](https://github.com/simbrain/NeuralNetworksCogSciBook/blob/1371c5da040ff388fde37e438f47b625a71e13f8/Transformers.tex#L1278)<!--/ref--> (caveman mode)** <!--ref:r072-->[§1.7 LLMs in Practice](https://github.com/simbrain/NeuralNetworksCogSciBook/blob/1371c5da040ff388fde37e438f47b625a71e13f8/Transformers.tex#L1270)<!--/ref-->: Caveman mode reminds me of Newspeak from *1984*, but it also reminds me of telegraphic speech in early language development. Telegraphic speech is often cited in nativist arguments, associated with Chomsky's idea of an innate universal grammar, because children keep a consistent word order even while dropping small function words. Caveman mode seems to do something similar: it keeps word order and critical words like "not" that change intent. Unlike Newspeak, which deliberately shrank vocabulary to limit which thoughts could be expressed, caveman mode keeps the critical meaning without censorship. The cognitive science element already seems to be addressed in <!--ref:r106-->[§1.6.4](https://github.com/simbrain/NeuralNetworksCogSciBook/blob/1371c5da040ff388fde37e438f47b625a71e13f8/Transformers.tex#L1100)<!--/ref--> with the Chomsky vs. statistical learning debate, since LLMs learned to do all of this from statistics alone.

**<!--ref:r073-->[Lines 1464-1486](https://github.com/simbrain/NeuralNetworksCogSciBook/blob/1371c5da040ff388fde37e438f47b625a71e13f8/Transformers.tex#L1464-L1486)<!--/ref--> (group chats/Society of Mind)** <!--ref:r074-->[§1.7.3 Agentic Systems](https://github.com/simbrain/NeuralNetworksCogSciBook/blob/1371c5da040ff388fde37e438f47b625a71e13f8/Transformers.tex#L1421)<!--/ref-->: I used to run automated group chats in SillyTavern where one model played several different characters speaking in ordered turns (or I could manually trigger a character to speak and skip the turn order). Interestingly, I don't remember the characters bleeding into each other's roles three years ago, unlike in one-on-one character-to-user chats. The related cognitive science concept is already noted briefly in the comments: Minsky's Society of Mind, in which a system is made of many simple agents coordinated by managers (here, the frontend's turn order, and me when I manually bypass it).

## General suggestions

The proposed chapter can follow how a cognitive system gets assembled: **learning → situating → remembering → acting**. Each step has a clear cognitive-science counterpart, and for each one the link has already been made in published work, which justifies treating this material as its own chapter rather than overflow from the transformer and alignment chapters.

A one-sentence thesis for the chapter: a large language model resembles one powerful brain system, and much of the recent progress has come from surrounding it with the other systems a mind needs.

| Step | AI layer | Cognitive-science counterpart | Key sources |
|---|---|---|---|
| Learning | Pretraining, then fine-tuning and RLHF | Slow neocortical learning; context-dependent memory; consolidation | McClelland et al. (1995); Zhou et al. (2023); Choi et al. (2025) |
| Situating | Prompts and system prompts | Schemas, frames and scripts; activated long-term memory; priming | Cowan (2019); Minsky (1974); Schank and Abelson (1977) |
| Remembering | Context window, RAG, lorebooks, compaction | Working memory; hippocampal episodic memory | Ji-An et al. (2024); Huang et al. (2025) |
| Acting | Harnesses, tools, agents, multi-agent systems | Many specialized brain systems; society of mind; global workspace | Mahowald et al. (2024); Sumers et al. (2024); Zhuge et al. (2023) |

### 1. Learning at different scales (fine-tuning)

Models learn broadly first, then learn specialized behavior, including behaving differently in different places, and both stages have direct parallels in memory research.

**Context-dependent memory.** In Godden and Baddeley's (1975) diver study, people recalled word lists better in the setting where they had learned them (underwater or on land). Code-switching, and acting differently at work and at home, belong here too. One caution: a 2021 exact replication by Murre did not find the effect, so it is safer to cite it alongside Tulving's broader encoding-specificity principle than on its own.

**Complementary learning systems (CLS).** McClelland, McNaughton and O'Reilly (1995) argued that the brain pairs a slow neocortical learner, which extracts general structure, with a fast hippocampal learner, which stores single episodes. Replay, especially during sleep, gradually moves episodes into the slow system without overwriting older knowledge. Recent papers map this onto LLMs: weights act as the slow system, the context window as the fast one, and fine-tuning as consolidation. A 2026 bioRxiv paper by Pan, Hahami, Siegelmann and Sompolinsky builds a complete CLS inside one language model, and notes that naive sequential fine-tuning overwrites earlier memories, which is the catastrophic-interference problem CLS was proposed to explain.

**Fine-tuning as learning which repertoire to express.** Meta's LIMA paper (Zhou et al., 2023) fine-tuned a 65B model on only 1,000 curated examples and got competitive results. The authors proposed the Superficial Alignment Hypothesis: knowledge comes almost entirely from pretraining, and fine-tuning mainly teaches which style or format to use. The hypothesis is disputed, which is useful material for the chapter in its own right.

**The link has already been made in the literature.** *Teaching LLMs How to Learn with Contextual Fine-Tuning* (Choi et al., ICLR 2025) fine-tunes LLMs with prompts modeled on how people study, such as linking new material to things already known. *Turning large language models into cognitive models* (Binz and Schulz) fine-tunes LLMs on psychology experiment data so they behave more like human participants.

**Emergent misalignment as a persona shift.** This is a strong modern case study for this section. Betley et al. (2025) found that fine-tuning a model on one narrow task, writing insecure code, made it broadly misaligned on unrelated questions. OpenAI's follow-up (2025) found a "misaligned persona" feature that controls the effect, and showed that a small amount of benign fine-tuning reverses it. Narrow training did not install a narrow skill; it shifted which character the model takes itself to be, which connects fine-tuning to identity and role learning rather than only to isolated behaviors.

### 2. Prompts as situational framing

A prompt tells the model what kind of situation it is in, much as "this is a serious event" or "this group pranks each other" tells a person how to behave.

**Schemas, frames and scripts.** Minsky's frames (1974) and Schank and Abelson's scripts (1977) proposed that people understand situations by calling up a stored structure of expectations; a restaurant script predicts a menu, ordering, eating and paying. A system prompt works like a frame selector. This also connects back to Minsky, who appears again in section 4. A notable contrast for the book: symbolic AI had to hand-build each frame, while LLMs seem to learn huge numbers of them implicitly from text.

**Activated long-term memory.** "Activated long-term memory" is the technical term from Nelson Cowan's embedded-processes model: working memory is the currently activated part of long-term memory, with a smaller focus of attention inside it, not a separate store (Cowan, 2019). A prompt similarly activates the relevant slice of what the model already knows; "be serious" does not teach seriousness, it calls up existing knowledge of how people act at serious events.

**In-context versus in-weight learning.** Russin, Pavlick and Frank (Brown University, PNAS) show that in-context learning runs in the network's activations, similar to working-memory models of prefrontal cortex, while training changes the weights the way synaptic learning does. They show that the interplay between the two reproduces human findings such as curriculum effects, and frame it as a new view of dual-process theories. This is a strong citation for the prompt-as-working-memory idea.

**Role play.** Shanahan, McDonell and Reynolds (*Nature*, 2023) describe a dialogue agent as role-playing the character its prompt describes, or as a superposition of possible characters narrowed down as a conversation goes on. This gives the chapter vocabulary for "acting differently in different places" without anthropomorphizing. It also connects to the role-token observations in the line-by-line notes.

**Prompt injection as a false framing of the situation.** The earlier draft flagged this angle as unconfirmed, but the literature does make it. A 2023 study (arXiv 2311.14876) applied Cialdini's persuasion principles, such as authority, reciprocity and social proof, to jailbreak major models and found them susceptible. Cohen and Heverin (ECCWS 2025) tested four social-engineering techniques as prompt injections and found impersonation the most effective. The TRAP benchmark (Korgul et al., 2025) found that web agents across six frontier models followed injected instructions in about 25% of tasks on average, and that persuasion framing strongly affected success. One explanation offered in this literature is that training text is full of cases where appeals to authority are followed by compliance, so models inherit a human-like susceptibility.

### 3. Context as memory

The context window behaves like memory in some ways and unlike it in others, and the chapter can present both sides.

**Context as episodic memory.** *Linking In-context Learning in Transformers to Human Episodic Memory* (Ji-An, Zhou and colleagues, NeurIPS 2024) finds that induction heads behave like the contextual maintenance and retrieval (CMR) model of human episodic memory, and that removing them impairs in-context learning.

**Context as working memory, and its limits.** Gong, Wan and Wang (AAAI 2024) gave ChatGPT n-back tasks and found a capacity limit that resembles the human one. For balance, *Language Models Do Not Have Human-Like Working Memory* (Huang, Sun, Wang and Dredze, 2025) argues that n-back tests are misleading because the model can simply re-read its visible context. Using tasks such as a number-guessing game, where the answer must be held internally, they found irrational or contradictory behavior across seventeen frontier models. Together, these papers suggest the context window is closer to an external notepad the model keeps consulting than to a human mind holding something in.

**The missing hippocampus.** In complementary-learning-systems terms, current models have the slow cortical learner but no true fast episodic system that later consolidates into the weights; retrieval tools approximate it from the outside.

**Engineering workarounds as memory aids.** The SillyTavern lorebook (entries inserted into the context when keywords appear) and the anterograde amnesia comparison fit here: the model cannot form new long-term memories after training, so the harness supplies cue-triggered notes, much like the external memory aids used by people with amnesia. RAG and context compaction belong in the same group.

### 4. Harnesses and the brain as many systems

The idea that an LLM models a single cortical patch or system, while the brain is a large collection of systems, has strong support, and it is close to a direct justification for harnesses.

**The LLM as the language network.** *Dissociating language and thought in large language models* (Mahowald, Ivanova, Blank, Kanwisher, Tenenbaum and Fedorenko, *Trends in Cognitive Sciences*, 2024) separates formal linguistic competence (getting the form of language right) from functional competence (using language to reason and act in the world). In people these depend on different brain networks. The authors argue that LLMs are good models of the language network but incomplete models of thought, and that reliable functional competence often requires adding systems beyond next-word prediction.

**A useful complication: modularity emerging inside the model.** *Modular Cognitive Architecture Emerges in Large Language Models* (Han, Andreas, Fedorenko and de Varda; arXiv 2608.13567, submitted June 2026) used circuit analysis on 46 tasks across four domains: language, formal reasoning, social reasoning and physical reasoning. In six open models from 24B to 123B parameters, tasks from the same human brain network recruited overlapping neurons, while tasks from different networks used largely separate ones. Lesioning the language neurons reportedly left reasoning intact while introducing spelling and agreement errors. This suggests a single model may already contain several brain-like systems, so the "single cortical patch" framing should be softened. It is still a preprint and has not been peer reviewed, so it should be presented as recent and preliminary.

**Cognitive architectures for agents.** *Cognitive Architectures for Language Agents* (CoALA; Sumers, Yao, Narasimhan and Griffiths, TMLR 2024) argues that LLMs resemble the production systems of classic AI, and that agent harnesses are rediscovering cognitive architectures such as Soar. CoALA describes an agent as having working, episodic, semantic and procedural memory, a set of actions, and a decision loop, which could organize the whole harness discussion.

**Society of Mind.** *Mindstorms in Natural Language-Based Societies of Mind* (Zhuge et al., with Schmidhuber, 2023) cites Minsky directly and builds societies of up to 129 communicating models that solve problems by questioning one another in natural language. The SillyTavern group-chat example from the line-by-line notes is a simple, concrete version of the same idea and could open this section.

**Global workspace theory.** Baars's theory says specialized modules compete for a limited workspace whose contents are broadcast to all of them. Goldstein and Kirk-Giannini (2024) argue that language-agent architectures, with a shared memory stream coordinated by an LLM, come close to this design. Their paper is about consciousness, which may be out of scope, but the architectural comparison is useful by itself.

| Harness component | Cognitive counterpart |
|---|---|
| Base LLM | Language network; semantic long-term memory |
| Context window and scratchpad | Working memory; global workspace |
| RAG, lorebooks and vector memory | External aids for episodic memory |
| Tools and code execution | Other specialized systems, such as calculation |
| Planner or orchestrator loop | Executive control |
| Multiple agents or characters | Society of mind |
| Skills and saved procedures | Procedural memory |

## Case studies

Each case pairs one AI finding with one cognitive-science idea, so it could serve as a boxed example in the chapter.

| Case study | What happened | Cognitive-science link | Section |
|---|---|---|---|
| Role bleed in SillyTavern | Older models sometimes wrote the user's turns; recent models with native role tokens did not | Source monitoring; self-other misattribution | 2 |
| SillyTavern group chats | One model played several characters in turn, coordinated by the frontend | Society of mind | 4 |
| Emergent misalignment | Narrow fine-tuning on insecure code produced broad misalignment, controlled by one persona feature | Identity and role learning | 1 |
| LIMA | 1,000 curated examples produced a competitive chat model | Pretraining as broad knowledge; fine-tuning as repertoire selection | 1 |
| Godden and Baddeley, and the replication | Context effect found in 1975, not found in a 2021 exact replication | Context-dependent memory; fragility of classic results | 1 |
| Number-guessing game | Models could not hold a secret number consistently | Working memory | 3 |
| Persuasion-based prompt injection | Authority and impersonation raised injection success; agents were fooled in about 25% of TRAP tasks | Social engineering | 2 |
| Language-neuron lesions | Removing language neurons kept reasoning but caused spelling and agreement errors | Language-thought dissociation | 4 |

Another idea for opening section 2: ask a model the same question under the "serious event" and "pranking group" framings, and show the two answers side by side.

## Cautions before citing

Each analogy has a known weak point, and naming it in the chapter will make the argument stronger.

- **Context window vs. working memory:** human working memory holds a handful of items, while context windows hold hundreds of thousands of tokens, and Huang et al. argue that models have no true internal working memory. "Functionally similar" is safer than "the same."
- **The Superficial Alignment Hypothesis is disputed:** LIMA relied on human preference ratings, and critics argued it overstated the result.
- **Classic findings can fail to replicate:** cite Murre's 2021 replication alongside Godden and Baddeley.
- **The modularity preprint is new:** Han et al. (2026) has not yet been peer reviewed.
- **Role-play language can slide into anthropomorphism:** Shanahan and colleagues introduced it specifically to avoid attributing human mental states to models.
- **First-hand SillyTavern observations are anecdotal:** they work well as illustrations, but claims about why role bleed stopped would need a source or a small test.

## Sources

Fine-tuning and learning:

- Choi et al. (2025). [Teaching LLMs How to Learn with Contextual Fine-Tuning](https://arxiv.org/abs/2503.09032). ICLR.
- Binz and Schulz. Turning large language models into cognitive models.
- Zhou et al. (2023). [LIMA: Less Is More for Alignment](https://ar5iv.labs.arxiv.org/html/2305.11206).
- OpenAI (2025). [Toward understanding and preventing misalignment generalization](https://openai.com/index/emergent-misalignment/). Builds on Betley et al. (2025).
- McClelland, McNaughton and O'Reilly (1995). Why there are complementary learning systems in the hippocampus and neocortex. *Psychological Review* 102(3).
- Pan, Hahami, Siegelmann and Sompolinsky (2026). [A complementary learning system for continual episodic memory in large language models](https://www.biorxiv.org/content/10.64898/2026.08.24.746712.full.pdf). bioRxiv.
- Godden and Baddeley (1975), *British Journal of Psychology* 66; replication by Murre (2021), [Royal Society Open Science](https://pmc.ncbi.nlm.nih.gov/articles/PMC8568063/).

Prompts and framing:

- Cowan (2019). [Short-term memory based on activated long-term memory](https://memory.psych.missouri.edu/assets/doc/articles/2019/cowan-2019-psych-bulletin-comment-on-norris---stm-as-activated-ltm.pdf). *Psychological Bulletin*.
- Minsky (1974), A framework for representing knowledge; Schank and Abelson (1977), *Scripts, Plans, Goals and Understanding*.
- Russin, Pavlick and Frank. [Parallel trade-offs in human cognition and neural networks](https://ski.clps.brown.edu/papers/Russin_ICL.pdf). PNAS.
- Shanahan, McDonell and Reynolds (2023). [Role play with large language models](https://www.nature.com/articles/s41586-023-06647-8). *Nature* 623.
- [Exploiting LLMs through deception techniques and persuasion principles](https://arxiv.org/pdf/2311.14876) (2023).
- Cohen and Heverin (2025). [Psychological prompt injection attacks](https://papers.academic-conferences.org/index.php/eccws/article/view/3515). ECCWS.
- Korgul et al. (2025). TRAP: Task-Redirecting Agent Persuasion Benchmark.

Context and memory:

- Ji-An, Zhou et al. (2024). [Linking In-context Learning in Transformers to Human Episodic Memory](https://arxiv.org/html/2405.14992v2). NeurIPS.
- Huang, Sun, Wang and Dredze (2025). [Language Models Do Not Have Human-Like Working Memory](https://arxiv.org/abs/2505.10571v3).
- Gong, Wan and Wang (2024). [Working memory capacity of ChatGPT](https://arxiv.org/pdf/2305.03731). AAAI.

Harnesses and many systems:

- Mahowald et al. (2024). [Dissociating language and thought in large language models](https://arxiv.org/abs/2301.06627). *Trends in Cognitive Sciences* 28(6).
- Han, Andreas, Fedorenko and de Varda (2026). [Modular Cognitive Architecture Emerges in Large Language Models](https://arxiv.org/pdf/2608.13567). Preprint.
- Sumers, Yao, Narasimhan and Griffiths (2024). [Cognitive Architectures for Language Agents](https://arxiv.org/abs/2309.02427). TMLR.
- Zhuge et al. (2023). [Mindstorms in Natural Language-Based Societies of Mind](https://arxiv.org/abs/2305.17066).
- Goldstein and Kirk-Giannini (2024). [A Case for AI Consciousness: Language Agents and Global Workspace Theory](https://arxiv.org/abs/2410.11407v1).
- [SillyTavern documentation](https://docs.sillytavern.app/).
