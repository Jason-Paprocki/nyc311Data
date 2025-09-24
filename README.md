# NYC 311 Data Explorer

Have you ever heard a distant siren or seen a blocked-off street and wondered what was going on? As a resident of New York City, I was always curious about the pulse of the city as told through its 311 service calls. This project was born from a simple desire to see what's happening in my neighborhood—and yours—in a quick, visual way.

What started as a personal tool grew into a project built with the reliability and security needed to be shared with fellow New Yorkers.

---

## ## Architecture Overview

This project is a modern, full-stack web application designed for performance and reliability. To ensure it runs smoothly and securely, it's built on a containerized architecture and deployed to the AWS cloud.

**High-Level Flow:**
A user's browser loads the **React** frontend from a high-speed Content Delivery Network (**AWS CloudFront**). When a user searches for an address, the app calls our **Python API**, which runs as a "serverless" container in **AWS ECS**. The API then securely queries our **PostgreSQL** database (**AWS RDS**) to fetch the relevant 311 data and returns it for display on the map.

---

## ## Technology & Purpose

Building a high-quality, public-facing application requires using the right tools for the job. Every technology here was chosen to make the final product more robust, secure, and efficient.

### ### Application & Data

* **React:** Chosen for its component-based architecture, making it ideal for building the complex and interactive map interface.
* **Leaflet:** A lightweight, open-source mapping library used to render the map and plot the 311 data points efficiently.
* **Python/FastAPI:** A modern, high-performance combination used to build our backend API. Its speed ensures that data is fetched and delivered to the user quickly.
* **PostgreSQL:** A powerful, open-source relational database used to store and efficiently query the large 311 dataset with geospatial capabilities.

### ### Infrastructure & Operations

* **Docker:** Provides a consistent and isolated environment for each part of the application, eliminating "it works on my machine" problems and streamlining development.
* **Terraform:** Manages our entire AWS cloud environment through code. This ensures our production infrastructure is stable, repeatable, and free from manual configuration errors.
* **AWS:** Provides the scalable, on-demand cloud infrastructure needed to run a reliable, public-facing web service.
* **AWS ECS on Fargate:** Runs our application containers without requiring server management. This allows the application to scale automatically based on traffic.
* **AWS RDS:** A managed PostgreSQL service. AWS handles backups, patching, and availability, ensuring our data is always safe and accessible.

### ### Quality & Security Automation

* **GitHub Actions:** The automation engine for the project. It automatically tests and scans every code change to guarantee that new features are safe and reliable before they reach users.
* **Security Scanners:** A suite of tools (**Bandit, Trivy, OWASP ZAP, tfsec**) are integrated into our pipeline. As a responsible developer, it's crucial to proactively scan for security vulnerabilities to ensure the application is safe for everyone.
* **AWS Secrets Manager:** Securely manages sensitive information like database credentials. This prevents secrets from being exposed in our codebase and is a critical security best practice.

---

## ## Project Workflow: From Code to Cloud

1.  **Local Development:** The project can be run locally in its entirety using **Docker Compose**, creating a perfect replica of the production environment.
2.  **Commit & Push:** When a new feature is ready, the code is pushed to **GitHub**.
3.  **Automated Quality Pipeline:** The push triggers a **GitHub Actions** workflow that automatically scans the code, builds fresh **Docker** images, and runs tests.
4.  **Automated Deployment:** On a successful merge to the `main` branch, a final pipeline deploys the changes to **AWS** via **Terraform** and **ECS** with zero downtime.
