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

- What constraints does your scheduler consider (for example: time, priority, preferences)?
- How did you decide which constraints mattered most?

**b. Tradeoffs**

- Describe one tradeoff your scheduler makes.
- Why is that tradeoff reasonable for this scenario?

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
