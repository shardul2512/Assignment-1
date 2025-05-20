# Insurance Claims Management System
A comprehensive solution for managing insurance policyholders and claims, with integrated risk analysis capabilities.

## 📋 Overview

This project provides a complete insurance claims management platform that enables insurance companies to:

- Manage policyholders and their information
- Process and track insurance claims
- Perform risk analysis on claims data
- Visualize claims trends and statistics

The system consists of a FastAPI backend API and a Streamlit web application frontend.

# 🏗️ Architecture

The application follows a client-server architecture:

1. **Backend API (`api.py`)**: FastAPI-powered REST API that handles data processing, database operations, and business logic
2. **Frontend UI (`app.py`)**: Streamlit web application that provides an intuitive user interface for interacting with the system

## ✨ Features

# Backend Features

- RESTful API built with FastAPI (version 1.2.1)
- Oracle database integration for data persistence
- Comprehensive data models for policyholders and claims
- Authentication and authorization
- Risk analysis algorithms
- Error handling and validation

# Frontend Features

- Modern, responsive UI built with Streamlit
- Custom styling with CSS for enhanced user experience
- Interactive dashboards with real-time data visualization
- Form-based interfaces for data entry and management
- Date-based filtering and reporting

## 🛠️ Tech Stack

### Backend:
- FastAPI framework
- Oracle database (via oracledb)
- Pydantic for data validation
- Python 3.8+

### Frontend:
- Streamlit
- Custom CSS
- Font Awesome icons
- Chart visualization libraries

## 🚀 Getting Started

### Prerequisites
- Python 3.8 or higher
- Oracle Database (local or remote instance)
- Required Python packages (see requirements.txt)

### Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/insurance-claims-system.git
cd insurance-claims-system
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows use: venv\Scripts\activate
```

3. Install the required dependencies:
```bash
pip install -r requirements.txt
```

4. Configure the Oracle database connection in `api.py`:
```python
DB_USER = "your_username"
DB_PASSWORD = "your_password"
DB_DSN = "your_host:your_port/your_service"
```

### Usage

#### Running the Backend API
1. Start the FastAPI server:
```bash
uvicorn api:app --reload
```

#### Running the Frontend Application
1. Start the Streamlit application:
```bash
streamlit run app.py
```
2. Access the web interface at http://localhost:8501

---

## 🔄 API Endpoints

The system provides the following API endpoints:

### Policyholders
- `GET /policyholders`: Retrieve all policyholders
- `POST /policyholders`: Create a new policyholder
- `GET /policyholders/{id}`: Retrieve a specific policyholder
- `PUT /policyholders/{id}`: Update a policyholder
- `DELETE /policyholders/{id}`: Delete a policyholder

### Claims
- `GET /claims`: Retrieve all claims
- `POST /claims`: Create a new claim
- `GET /claims/{id}`: Retrieve a specific claim
- `PUT /claims/{id}`: Update a claim
- `DELETE /claims/{id}`: Delete a claim

### Analytics
- `GET /analytics/risk`: Perform risk analysis on claims data
- `GET /analytics/trends`: Get claims trends and statistics

## 💾 Database Schema

The system uses the following database schema:

- **Policyholders Table**: Stores information about insurance policyholders
- **Claims Table**: Stores information about insurance claims
- **Risk Factors Table**: Stores risk factors associated with claims

## 🧪 Core Functionality

### Policyholder Management
- Create, read, update, and delete policyholder records
- Store policyholder personal information and policy details
- Track policy history and changes over time

### Claims Processing
- Submit new insurance claims with supporting details
- Process claims through various status stages
- Associate claims with specific policyholders and policies
- Track claim resolution and payment information

### Risk Analysis
- Calculate risk factors based on claim history
- Identify potentially fraudulent claim patterns
- Generate risk scores for policyholders and claim types

### Reporting and Analytics
- Visualize claim trends over time
- Generate reports on claim frequency and severity
- Analyze claim distribution by policy type and other factors

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Commit your changes: `git commit -m 'Add some feature'`
4. Push to the branch: `git push origin feature-name`
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 👏 Acknowledgements

- FastAPI for the powerful API framework
- Streamlit for the intuitive web application framework
- Oracle for the reliable database system

Created by Shardul Pande
