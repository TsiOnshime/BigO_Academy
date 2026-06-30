<h1 align="center">BigO_Academy</h1>

<p align="center">
  A production-grade, microservices-based learning management platform built to digitize and scale the operations of <strong>A2SV (Africa to Silicon Valley)</strong>.
</p>

<p align="center">
  <strong>Microservices • Event-Driven Architecture • Hexagonal Architecture • Apache Kafka • PostgreSQL</strong>
</p>

---

## Overview

<p>
The A2SV Community Platform manages the complete lifecycle of A2SV's engineering training program—from student admission and curriculum delivery to performance tracking, mentorship, contest management, and graduation.
</p>

<p>
The platform replaces manual workflows with an automated, data-driven system that serves students, teachers, and administrators through role-based interfaces.
</p>

<p>
Built as a distributed system, it follows modern software engineering practices including:
</p>

<ul>
  <li>Microservices Architecture</li>
  <li>Hexagonal Architecture (Ports & Adapters)</li>
  <li>Event-Driven Communication</li>
  <li>Domain-Driven Design (DDD)</li>
  <li>Choreography-Based Saga Pattern</li>
  <li>Outbox Pattern</li>
</ul>

---

## Services

<table>
  <tr>
    <th>Service</th>
    <th>Responsibility</th>
  </tr>
  <tr>
    <td><strong>Auth Service</strong></td>
    <td>JWT Authentication, Google OAuth, GitHub OAuth, Role Management</td>
  </tr>
  <tr>
    <td><strong>Academic Service</strong></td>
    <td>Students, Cohorts, Curriculum, Attendance, Contests, Mentorship, Warnings</td>
  </tr>
  <tr>
    <td><strong>Analytics Service</strong></td>
    <td>Rankings, Leaderboards, Performance Scores, Consistency Metrics, Reporting</td>
  </tr>
  <tr>
    <td><strong>Payment Service</strong></td>
    <td>Student Subscriptions, Teacher Payments, Financial Reporting</td>
  </tr>
</table>

---

## System Architecture

<pre>
                        ┌─────────────────┐
                        │   Auth Service  │
                        │   (JWT + OAuth) │
                        └────────┬────────┘
                                 │
                    JWT validated by all services
                                 │
                    ┌────────────┼────────────┐
                    │            │            │
           ┌────────▼───┐  ┌────▼──────┐  ┌──▼────────────┐
           │  Academic  │  │  Payment  │  │   Analytics   │
           │  Service   │  │  Service  │  │   Service     │
           └────────────┘  └───────────┘  └───────────────┘
                    │            │                ▲
                    └────────────┴────────────────┘
                              Kafka
                 (Event-Driven Communication Layer)
</pre>

<p>
Each service owns its own PostgreSQL database and communicates asynchronously through Apache Kafka. Services never access each other's databases directly, ensuring strong service boundaries and loose coupling.
</p>

---

## Technical Highlights

<ul>
  <li><strong>Hexagonal Architecture</strong> — Business logic is completely isolated from frameworks, databases, and messaging infrastructure.</li>

  <li><strong>Event-Driven Communication</strong> — Services communicate asynchronously through Apache Kafka, improving scalability and resilience.</li>

  <li><strong>Role-Based Access Control</strong> — Fine-grained authorization for Students, Teachers, and Administrators.</li>

  <li><strong>Automated Warning Engine</strong> — Monitors attendance, problem-solving activity, and contest participation while automatically escalating repeated violations.</li>

  <li><strong>Real-Time Analytics</strong> — Continuously updates leaderboards, rankings, consistency scores, and cohort performance reports.</li>

  <li><strong>JWT Authentication</strong> — Short-lived access tokens with rotating refresh tokens plus Google and GitHub OAuth support.</li>

  <li><strong>Outbox Pattern</strong> — Guarantees reliable event delivery between services even under failure conditions.</li>

  <li><strong>Historical Metrics Snapshots</strong> — Daily snapshots support trend analysis, growth tracking, and reporting.</li>
</ul>

---

## Domain Highlights

<ul>
  <li>
    <strong>Cohort-Based Learning Program</strong>
    <ul>
      <li>Year 1: Data Structures & Algorithms, Competitive Programming</li>
      <li>Year 2: System Design, Projects, and Interview Preparation</li>
    </ul>
  </li>

  <li>
    <strong>Curriculum Management</strong>
    <ul>
      <li>DSA Topics</li>
      <li>LeetCode Problem Sets</li>
      <li>Codeforces Problem Sets</li>
      <li>Per-Student Progress Tracking</li>
    </ul>
  </li>

  <li>
    <strong>Contest Management</strong>
    <ul>
      <li>Weekly Contests</li>
      <li>Participation Tracking</li>
      <li>Rankings and Performance Contribution</li>
    </ul>
  </li>

  <li>
    <strong>Mentorship System</strong>
    <ul>
      <li>Teacher-Student Assignments</li>
      <li>Session Scheduling</li>
      <li>Progress Monitoring</li>
    </ul>
  </li>

  <li>
    <strong>Student Lifecycle Management</strong>

<pre>
Admission
    ↓
Active Student
    ↓
Probation
    ↓
Promotion to Year 2
    ↓
Graduation
</pre>

  </li>
</ul>

---

## Tech Stack

<table>
  <tr>
    <th>Layer</th>
    <th>Technology</th>
  </tr>
  <tr>
    <td>Backend</td>
    <td>Python, Django, Django REST Framework</td>
  </tr>
  <tr>
    <td>Database</td>
    <td>PostgreSQL</td>
  </tr>
  <tr>
    <td>Message Broker</td>
    <td>Apache Kafka</td>
  </tr>
  <tr>
    <td>Authentication</td>
    <td>JWT (SimpleJWT), Google OAuth, GitHub OAuth</td>
  </tr>
  <tr>
    <td>Task Scheduling</td>
    <td>Celery, Celery Beat</td>
  </tr>
  <tr>
    <td>Architecture</td>
    <td>Microservices, Hexagonal Architecture, DDD</td>
  </tr>
  <tr>
    <td>API Specification</td>
    <td>OpenAPI 3.0</td>
  </tr>
</table>

---

## API Documentation

<p>
Each service exposes a fully documented OpenAPI 3.0 specification. See the <code>docs/</code> directory inside each service for complete API definitions.
</p>

---

## Local Development

```bash
docker-compose up
```

Each service can also be run independently. Refer to the README inside each service directory for setup instructions.

---

## About A2SV

<p>
<strong>Africa to Silicon Valley (A2SV)</strong> is a non-profit organization based at Addis Ababa University that identifies high-potential African students, trains them in competitive programming and software engineering, and connects them with internship and full-time opportunities at leading technology companies.
</p>

<p>
Alumni have gone on to work at Google, Meta, Amazon, Microsoft, Palantir, and other top technology companies.
</p>

<p>
This platform was built to support and scale that mission through modern distributed systems and data-driven educational infrastructure.
</p>
