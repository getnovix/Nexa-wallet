Nexa Wallet

A Sudan-focused financial platform built independently by a young developer.

Nexa is a project I started because I wanted to build something useful, not just another small tutorial project. My idea is to create a platform where people can manage their digital balances, make transfers, trade digital products, use a marketplace, and eventually exchange assets through a P2P system.

The project is still under development. Some parts are implemented, some are being improved, and others are not finished yet. I prefer to be honest about that instead of presenting Nexa as a complete financial product when there is still work to do.

GitHub: https://github.com/getnovix/Nexa-wallet

---

About the project

Nexa is intended to become a financial and digital services platform designed with the needs of users in Sudan in mind, with the possibility of expanding to other markets in the future.

The long-term idea is to bring different services together in one place:

- Digital wallets and balance management.
- Transfers between users.
- Transaction history and related financial operations.
- A digital products store.
- A marketplace for products and merchants.
- Peer-to-peer (P2P) trading.
- User profiles and account management.
- Notifications and communication between users.
- Administrative tools for managing the platform.

These are the goals of the project, not a claim that every feature is already production-ready.

Why I started Nexa

My name is Ibrahim. I am an 18-year-old developer from Sudan.

I started learning programming at a young age, and over time I became interested in backend development, APIs, databases, authentication, and financial systems.

My circumstances have not always been easy. Financial difficulties have affected my education, the equipment I can afford, and the amount of time I can dedicate to development. I have had to balance work and personal responsibilities while continuing to learn and build.

I am working on Nexa independently. That means I am not only writing features, but also learning how to design the database, structure the backend, handle errors, think about security, and understand how the different parts of a real application should work together.

I still have a lot to learn. I do not consider myself an expert, and I know that building a financial platform requires much more than making endpoints work. But I want to keep improving the project and use it to demonstrate what I can do as a backend developer.

For me, Nexa is both a product idea and a practical learning experience.

Technology stack

The current repository is primarily written in Python.

The technologies and concepts used or planned for the project include:

- Python — backend development.
- FastAPI — API routing and request handling.
- PostgreSQL — relational data storage in the planned/current database architecture.
- JWT — token-based authentication.
- Pydantic — request validation and structured data.
- Environment variables — configuration and sensitive settings.
- REST API design — separating features into different modules.

The exact dependencies and supported versions are defined in "requirements.txt". The project should be tested with the dependency versions and environment configuration used by the developer.

Project structure

The repository is divided into modules so that different parts of the application can be developed and maintained separately.

"main.py"

The main application entry point. It is responsible for bringing the backend application and its routes together.

"auth.py"

Authentication-related functionality. Authentication is an important part of Nexa because account access must be handled carefully, especially when the platform deals with balances and transactions.

"users.py"

User-related operations and account functionality.

"profile.py"

Profile-related features. This module is intended to keep profile operations separate from the core authentication and transaction logic.

"database.py"

Database connection and database-related functionality. Keeping database operations organized makes it easier to maintain the application as the number of features grows.

"wallets.py"

Wallet-related operations. This module belongs to the part of Nexa responsible for representing and managing user wallets.

"transactions.py"

Transaction-related functionality. Financial operations require special attention to validation, consistency, error handling, and preventing incorrect balance changes.

"validators.py"

Validation helpers used to check input before it is processed. Validation is important because API requests cannot be assumed to contain correct or trustworthy data.

"marketplace.py"

Marketplace functionality. The intended marketplace allows the platform to support products, merchants, and related purchasing workflows.

"digital_store.py"

Digital products and store-related functionality. This is intended to support digital services and products separately from the general marketplace logic.

"store.py"

Additional store-related operations. The store modules are separated to keep the code organized as these features evolve.

"admin.py"

Administrative functionality for managing parts of the platform. Administrative access needs stricter authorization than ordinary user access.

"p2p.py"

The peer-to-peer trading module. This is one of the more complex parts of Nexa and is still being developed and reviewed.

"chat.py"

The chat module. The goal is to support communication between users, particularly in workflows where users need to discuss an order or resolve a transaction-related issue. The implementation is not yet complete.

"chat_bot.py"

A separate module for chatbot-related functionality.

"config.py"

Application configuration. Sensitive values should be supplied through environment variables rather than committed directly to the repository.

"requirements.txt"

The Python dependencies required by the application.

The module names describe the intended responsibilities of the files. They do not, by themselves, guarantee that all associated functionality is complete.

P2P trading: why "p2p.py" is not finished

P2P is not just a page where one user sells and another user buys. A reliable P2P system has to coordinate several related operations without allowing money or transaction states to become inconsistent.

For Nexa, I want the P2P system to support a workflow where users can publish offers, create orders, communicate about an order, and complete a trade under clearly defined rules.

Some of the main areas that still need implementation, integration, or verification are:

- Merchant applications and approval.
- P2P advertisements and offer management.
- Order creation and valid order-state transitions.
- Reserving or holding funds while an order is active.
- Releasing or refunding held funds according to the final order state.
- Handling payment evidence and order disputes.
- Preventing duplicate processing of the same operation.
- Protecting against unauthorized changes to order status.
- Managing timeouts, cancellations, and failed operations.
- Testing concurrent requests and database transactions.

The reason this module is taking time is that a mistake in P2P can affect real balances. I do not want to connect all the features together before the financial rules are clear and tested.

I also want P2P to remain separate from the general marketplace. Buying a product from a store and trading directly with another user are different workflows, and mixing their business logic would make the project harder to maintain.

The current "p2p.py" file is part of this ongoing work. Its presence should not be interpreted as proof that the entire P2P service is complete or safe for real-money trading.

Chat: why "chat.py" is not finished

The chat system is another feature that depends on other parts of the platform.

My intention is for chat to be useful rather than just a basic messaging screen. For example, a buyer and seller may need to communicate about a P2P order, while an order dispute may require access to the correct conversation and its history.

Before considering this feature complete, the system needs clear rules for:

- Identifying the participants in a conversation.
- Associating a conversation with the correct order when required.
- Ensuring that only authorized users can access messages.
- Storing and retrieving message history.
- Handling message delivery and failures.
- Preventing users from accessing another user's private conversations.
- Connecting chat to P2P order states and dispute workflows.

Real-time communication may also require additional infrastructure and testing, depending on the final implementation.

I have not finished this module because I want its access rules and relationship with the P2P system to be clear before treating it as a completed feature. Finishing the file itself is not enough; the full workflow must work correctly with the rest of the application.

Database and financial integrity

A financial application needs reliable data handling.

Nexa's database design must support users, balances, transactions, orders, products, and other related records without allowing invalid states to occur.

Areas that need particular attention include:

- Database constraints and relationships.
- Atomic financial operations.
- Preventing a balance from becoming negative where this is not permitted.
- Preventing duplicate transaction processing.
- Maintaining a consistent record of financial changes.
- Handling failures without leaving partially completed operations.
- Applying appropriate authorization before sensitive database changes.

These requirements are important whether Nexa is used by a small group of testers or eventually serves a larger number of users.

Security considerations

Security is an ongoing part of development, not something that can be completed simply by adding authentication.

The areas I intend to strengthen and verify include:

- Password storage and authentication.
- JWT validation and token expiration.
- Authorization checks for user-owned resources.
- Validation of incoming requests.
- Protection of environment variables and database credentials.
- Safe handling of administrative permissions.
- Rate limiting and abuse prevention.
- Logging that does not expose passwords, tokens, or sensitive financial data.
- Testing of financial operations and permission boundaries.

Nexa is a work in progress. It has not been independently audited, and this repository should not be treated as a security certification.

Do not use the current project to hold real customer funds or conduct real-money trading until the relevant functionality, security controls, and operational requirements have been independently reviewed and tested.

Current status

Nexa is under active development.

The repository contains separate modules for authentication, users, profiles, wallets, transactions, stores, marketplace functionality, administration, P2P, and chat.

However, not all modules have the same level of completion. Some functionality needs additional implementation, integration, testing, or review. I am continuing to work through these areas rather than claiming that the full platform is ready for production.

My current priorities are:

1. Review and stabilize the existing backend.
2. Improve validation, authentication, and authorization.
3. Verify database consistency and financial transaction handling.
4. Complete the P2P order and held-funds workflows.
5. Integrate chat with the appropriate user and order permissions.
6. Add tests for important success and failure cases.
7. Improve documentation and deployment configuration.

What I am learning through Nexa

Building this project has pushed me to think beyond individual Python functions.

I am learning how backend modules depend on one another, how database decisions affect business logic, why financial operations need careful transaction handling, and why security and testing must be considered throughout development.

I have also learned that a feature can look finished while still having important edge cases that have not been handled. That is one of the reasons I am documenting unfinished parts instead of hiding them.

Contributing and feedback

Nexa is currently a personal development project. I welcome constructive feedback, particularly about backend architecture, API design, database consistency, authentication, testing, and security.

If you review the project and notice an issue, please explain the problem and, if possible, include a reproducible example.

Final note

I am building Nexa with the resources available to me and improving it as I learn.

It is not a finished financial platform yet, and I am not claiming otherwise. There is still work to do, particularly around P2P trading, chat integration, testing, and security.

I am sharing the project because I want my work to be visible, learn from other developers, and continue growing as a Python backend developer.

Built in Sudan by Ibrahim.

GitHub: https://github.com/getnovix/Nexa-wallet

---

Backend Reliability Improvement: Post-Commit Exception Handling

During a review of Nexa's internal transfer logic, I identified an important reliability issue involving Python's "try" / "except Exception" handling after database transactions.

The issue

The original implementation placed the financial transaction and subsequent operations inside a single "try" block.

After successfully executing the financial operations and calling "conn.commit()", additional operations were performed, including balance updates and API response preparation.

If an exception occurred after the commit, the outer "except Exception" handler could catch it, execute "conn.rollback()", and return an error response.

However, the database transaction had already been committed.

At that point, calling "rollback()" could not reverse the completed financial operation.

Why this matters

The main problem is the inconsistency between the actual transaction result and the response presented to the user.

For example:

- A user initiates a transfer.
- The database successfully processes and commits the transfer.
- A subsequent operation raises an exception.
- The API returns a failure message even though the transfer succeeded.

This can negatively affect user trust and the perceived reliability of the platform.

Users may believe that Nexa is unstable, that transfers frequently fail, or that something is wrong with the platform's financial system.

It may also lead users to retry operations unnecessarily.

The improvement

The proposed solution is to separate post-commit operations from the main financial transaction's exception handling.

The database transaction should be handled independently, while operations performed after a successful commit should have their own error-handling logic.

This ensures that an exception occurring after a successful financial commit does not incorrectly cause the API to report the transfer as failed.

The approach also needs to preserve proper idempotency so that repeated requests cannot create duplicate financial operations.

What I learned

This investigation reinforced an important backend engineering principle:

The actual database transaction result must remain consistent with the result communicated to the user.

A committed financial operation must not be reported as failed simply because a subsequent non-transactional operation encountered an exception.

I am continuing to review similar exception-handling patterns across Nexa to improve its reliability and user experience.

---
