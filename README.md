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


# NYC 311 Data Visualization Project

This project is a full-stack web application designed to ingest, store, and visualize 311 complaint data for New York City. It serves as a portfolio piece demonstrating skills in data engineering, backend and frontend development, and DevSecOps practices.

## Project Plan & Status

### Phase 1: Data Ingestion

The goal of this phase is to reliably fetch data from the NYC OpenData API and store it in a persistent database.

- [x] **1A: Dockerize the Python Ingestion Script**
  - Create a `Dockerfile` for the Python script.
  - Ensure the base image (`python:3.9-slim`) can be pulled and the container builds successfully.
- [ ] **1B: Set up the PostgreSQL Database**
  - Create a `docker-compose.yml` file.
  - Define a `postgres` service with a persistent volume for data.
  - Manage database credentials securely.
- [ ] **1C: Connect Python to Postgres**
  - Update the Python script to connect to the Postgres container using Docker's internal networking.
  - Implement the logic to insert the fetched 311 data into the database.

### Phase 2: Backend API

This phase involves creating a simple API to serve the stored data to a front-end client.

- [ ] **2A: Build a "Skeleton" API**
  - Create a new service in `docker-compose.yml` for the API (e.g., using Flask or FastAPI).
  - Implement a single, simple endpoint (e.g., `/api/complaints/latest`) that retrieves and returns the 10 most recent complaints from the Postgres database.
- [ ] **2B: Expand API Functionality**
  - Add more complex endpoints as needed by the front-end (e.g., filtering by borough, complaint type, or date range).

### Phase 3: Frontend UI

This phase focuses on building a user interface to visualize the data provided by the API.

- [ ] **3A: Build a "Skeleton" Frontend**
  - Create a new service in `docker-compose.yml` for a simple frontend application.
  - Create a basic page that successfully calls the `/api/complaints/latest` endpoint and displays the data in a list or table.
- [ ] **3B: Develop Visualizations**
  - Add maps, charts, and graphs to visualize the 311 data.
  - Implement UI controls (like dropdowns and date pickers) to interact with the expanded API functionality.

### Phase 4: Orchestration & Security (DevSecOps)

This ongoing phase involves ensuring the entire application is robust, secure, and easy to manage.

- [ ] **4A: Full Orchestration**
  - Ensure all services (`ingestor`, `db`, `api`, `frontend`) can be launched and networked together with a single `docker compose up` command.
- [ ] **4B: Security Hardening**
  - Scan container images for vulnerabilities.
  - Implement proper secrets management for all credentials (e.g., using Docker secrets or a vault).
  - Configure container networking for least-privilege access.
- [ ] **4C: CI/CD Pipeline (Optional)**
  - Set up a basic CI/CD pipeline (e.g., using GitHub Actions) to automatically build, test, and deploy the application.
