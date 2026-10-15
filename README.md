# KugzyJobs – Video Editor Hiring Platform

## Project Overview

KugzyJobs is a web-based platform developed to connect content creators with freelance video editors. The system provides a centralized environment where creators can advertise editing opportunities, review applications, and communicate with editors.

The project aims to address challenges associated with finding suitable video editors, managing job applications, and evaluating editors based on their skills and portfolios.

KugzyJobs was developed as a final-year Computer Science project at Strathmore University.

## Problem Statement

With the growth of digital content creation on platforms such as YouTube, TikTok, Twitch, and Instagram, the demand for freelance video editors has increased.

However, content creators often experience difficulties identifying editors whose skills and editing styles match their requirements. Similarly, freelance editors may struggle to discover relevant opportunities and demonstrate their capabilities.

KugzyJobs addresses these challenges through a specialized hiring platform with structured job postings, editor portfolios, applications, and natural language processing (NLP) support.

## Project Objectives

1. Develop a web-based platform connecting content creators and video editors.
2. Enable creators to post video-editing jobs and manage applications.
3. Allow editors to create profiles and showcase their portfolios.
4. Implement NLP-based extraction of relevant skills, styles, and content niches from job descriptions.
5. Provide communication and administrative features to support the hiring process.
6. Evaluate the system through functional, database, and NLP testing.

## Main Features

### User Authentication
- User registration and login
- Different account roles for creators, editors, and administrators
- Role-specific functionality

### Creator Features
- Create and manage job advertisements
- View applications submitted by editors
- Access editor information and portfolios
- Communicate with editors

### Editor Features
- Create and manage editor profiles
- Showcase portfolio information
- Browse available editing jobs
- Apply for relevant opportunities
- Communicate with creators

### Natural Language Processing
- Analyze job descriptions
- Identify video-editing skills
- Extract editing styles and content niches
- Support structured interpretation of job requirements

### Administrative Features
- Administrative management interfaces
- User and platform oversight
- Support for managing platform reports

### Additional Platform Components
- Messaging
- Ratings
- Payment-related models and interfaces

Some integrations and workflows may require further configuration or testing before production deployment.

## Technologies Used

| Technology | Purpose |
|---|---|
| Python | Backend programming |
| Flask | Web application framework |
| Flask-SQLAlchemy | Database integration |
| SQLite | Local development database |
| HTML, CSS, JavaScript | Frontend development |
| Jinja2 | Server-side template rendering |
| spaCy | Natural language processing |
| Git | Version control |
| GitHub | Source code hosting |

## Project Structure

```text
KugzyJobs-Hiring-Project/
├── app/
│   ├── admin/
│   ├── authentication/
│   ├── creator/
│   ├── editor/
│   ├── main/
│   ├── models/
│   └── nlp/
├── data/
├── documentation/
├── utilities/
├── config.py
├── flasky.py
├── requirements.txt
├── .gitignore
└── README.md
```

## Installation and Setup

### 1. Clone the repository

```bash
git clone https://github.com/RyanMugele/KugzyJobs-Hiring-Project.git
cd KugzyJobs-Hiring-Project
```

### 2. Create a virtual environment

```bash
python3 -m venv venv
```

Activate it on macOS or Linux:

```bash
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment variables

Create a `.env` file in the project root and configure the environment variables required by `config.py`.

These may include the application secret key, email configuration, database credentials, and payment-service credentials.

Do not commit `.env` files or real credentials to GitHub.

### 5. Start the application

From the project root, run:

```bash
python flasky.py
```

The local application is intended to be accessed through the development server, typically at:

```text
http://127.0.0.1:5000
```

Additional database initialization or NLP model setup may be required depending on the local configuration.

## NLP Implementation

KugzyJobs includes an NLP component that analyzes video-editing job descriptions.

The implementation uses spaCy and phrase-matching techniques to identify relevant terminology in three categories:

- **Skills:** Editing-related technical abilities
- **Styles:** Editing approaches and presentation styles
- **Niches:** Content categories and subject areas

The extracted information helps organize job requirements into structured data.

This implementation uses rule-based NLP techniques rather than a separately trained machine-learning recommendation model.

## Testing

The project includes Python scripts for evaluating system components, including:

- `test_nlp.py`
- `test_nlp_functional.py`
- `test_nlp_database.py`

Testing focuses on NLP extraction, functional behavior, and database-related operations.

## Security Considerations

The application includes role-based functionality and authentication-related components.

Sensitive configuration values should be stored in environment variables rather than hardcoded in source files.

Before production deployment, the application should undergo additional security testing and configuration review.

## Future Improvements

Potential future enhancements include:

- More advanced editor-to-job recommendation algorithms
- Expanded portfolio authenticity verification
- Improved real-time collaboration features
- Further payment integration and testing
- Deployment to a production hosting environment

## Academic Information

**Project:** KugzyJobs – Video Editor Hiring Platform  
**Programme:** Bachelor of Science in Informatics and Computer Science  
**Institution:** Strathmore University  
**Project Type:** Final Year Project

## Author

Ryan Wesly Mugele

GitHub: https://github.com/RyanMugele

## License

License information will be added separately.