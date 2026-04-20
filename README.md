# Referee — Coffee Payment Queue

## 💡 Idea
>My friend and I always argue about whose turn it is to pay for coffee.  
>She is usually very kind, but at that moment very aggressively insists on treating me 😅
>Referee solves this in a simple way — it keeps track of turns so there are no doubts.

### Check it out 👉🏻 [Referee](https://site--referee--2sln2j6hvx4f.code.run/)

## 🔎 Overview
Mobile-oriented web application focused on clean data modeling and backend workflow design.
The system is built to be simple and practical, tailored to real user needs.

## ✔️ Key Features
- Group-based interaction using invite codes
- Owner-controlled group management
- Consistent state synchronization across multiple clients
- Instant UI updates via WebSockets (Django Channels)

## 🏛 Architecture & Design
>The backend is built with Django, combining:
>- Django templates for server-rendered views
>- Django REST Framework for API endpoints handling client-side interactions
>- Django Channels for real-time updates via WebSockets
>
>PostgreSQL is used as the primary data store.

Key design considerations:
- Keep the domain model simple and user-focused
- Designing data models for shared group state and interactions
- Implementing real-time communication patterns
- Modular architecture enabling iterative improvements based on user feedback