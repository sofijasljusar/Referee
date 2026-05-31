# Referee — Coffee Payment Queue

## 💡 Idea
>My friend and I always argue about whose turn it is to pay for coffee.  
>She is usually very kind, but at that moment very aggressively insists on treating me 😅
>Referee solves this in a simple way — it keeps track of turns so there are no doubts.

### Check it out 👉🏻 [Referee](https://site--referee--2sln2j6hvx4f.code.run/)

## 🔎 Overview
Mobile-oriented web application built around a **shared mutable state problem**.

Multiple users interact with the same payment queue simultaneously, 
requiring consistent state management, real-time synchronization, and protection against race conditions.

## ✔️ Key Features
- Group-based payment queues using invite codes 
- Owner-controlled group management 
- Real-time updates via WebSockets (Django Channels)
- Automatic owner transfer when the current owner leaves 
- Consistent state synchronization across connected clients

## ⚙️ Concurrency & Consistency
*The application manages shared group state where multiple users may perform actions concurrently.* 

> To ensure correctness under concurrent access:
>- Database transactions (transaction.atomic)
>- Row-level locking (select_for_update)
>- Database constraints enforcing queue integrity
>- Atomic state transitions for queue operations
>- Explicit handling of concurrent join, leave, close, reorder, and payer-change operations

> Design goals:
>- Prevent race conditions
>- Maintain queue integrity
>- Guarantee a single source of truth for all connected clients

## 🧪 Testing
The project includes:
- Service-layer tests
- API tests
- Persistence tests
- Concurrency tests

Concurrency scenarios were developed using a test-first mindset and validated through multi-threaded transactional
tests to verify correctness under race conditions.

## 🏛 Architecture
The backend is built with Django using:
- Django Templates
- Django REST Framework
- Django Channels

Key architectural decisions:
- Thin views, business logic isolated in a service layer
- Domain-specific exceptions
- Event-based real-time notifications
- Modular design enabling iterative improvements based on user feedback
