# PawPal+ Project Reflection

## 1. System Design

The current system design focuses on three core user actions that match the MVP goals for PawPal+.

1. Add a pet
- The user can create a pet profile by entering the pet's name, species, and age.
- The app stores this profile in session state so it can be used by later actions.
- This action establishes the primary entity in the system, and all care tasks are associated with that pet.

2. Schedule a walk
- The user can schedule a walk task by selecting a date, time, duration, and priority.
- Before creating the task, the app checks whether a pet profile exists.
- If no pet has been added, the app blocks scheduling and shows a clear message.
- If a pet exists, the app creates a structured walk task and saves it in the task list.

3. See today's tasks
- The app filters the stored task list to only show tasks scheduled for the current date.
- This gives the user a focused daily view instead of a full history.
- If no tasks exist for today, the app communicates that state clearly.

Design note: this first implementation uses Streamlit session state as the storage layer and keeps logic close to the UI to deliver a working vertical slice quickly. A next iteration can extract these behaviors into dedicated classes (such as Pet, Task, and Scheduler) for stronger separation of concerns and easier testing.

---

## 2. Scheduling Logic and Tradeoffs

**a. Constraints and priorities**

The scheduler considers three constraints: time (when a task is scheduled and how long it runs), priority (high / medium / low), and the owner's available minutes per day. When sorting, priority is applied first so high-urgency tasks like medication always appear before low-urgency ones like grooming, then time breaks ties within the same priority band. Available minutes was treated as a soft cap — the scheduler surfaces the total against the budget but does not hard-block tasks that exceed it, since pet care tasks often cannot simply be skipped.

**b. Tradeoffs**

The conflict resolver uses a single-pass greedy strategy: it sorts tasks by priority, then shifts each lower-priority task to start exactly when the higher-priority one ends. This is fast and predictable but can create a cascade — pushing task B may cause B to now overlap C, which is not re-checked. The tradeoff is reasonable here because most pet care schedules are sparse (a handful of tasks per day), so multi-level cascades are rare in practice, and the simplicity makes the behavior easy to explain to the owner.

---

## 3. AI Collaboration

**a. How you used AI**

- How did you use AI tools during this project (for example: design brainstorming, debugging, refactoring)?
- What kinds of prompts or questions were most helpful?

**b. Judgment and verification**

- Describe one moment where you did not accept an AI suggestion as-is.
- How did you evaluate or verify what the AI suggested?

---

## 4. Testing and Verification

**a. What you tested**

- What behaviors did you test?
- Why were these tests important?

**b. Confidence**

- How confident are you that your scheduler works correctly?
- What edge cases would you test next if you had more time?

---

## 5. Reflection

**a. What went well**

- What part of this project are you most satisfied with?

**b. What you would improve**

- If you had another iteration, what would you improve or redesign?

**c. Key takeaway**

- What is one important thing you learned about designing systems or working with AI on this project?
