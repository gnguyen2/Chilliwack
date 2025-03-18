# Chilliwack

## **Setup and Installation**
### **1. Clone the Repository**
```bash
git clone https://github.com/gnguyen2/Chilliwack.git
cd Chilliwack
```

### **2. Create a Virtual Environment (Recommended)**
```bash
python -m venv venv
source venv/bin/activate  # On Mac/Linux
venv\Scripts\activate  # On Windows
```
### **3. Install Dependencies**
```bash
pip install -r requirements.txt
```

### **4. Configure Environment Variables**
create a local .env file and reach out to @kjx172, @yuelex, @gia1103, or @d00mb0i on discord for the information to put inside your environment file


## **Running the Application**

### **1. Initialize the Database**
Run database migrations:
```bash
flask db init
flask db migrate -m "Initial migration"
flask db upgrade
```

### **2. Run Flask Application**
Run database migrations:
```bash
flask run
```
The app will be available at:
🔗 http://127.0.0.1:5000/

### **3. Testing Functionality**
You can use the temp admin script to change your role to test some of the role restricted functionality, there is also currently a link on the regular dashboard that will take you to the admin dash board as a basic user. It will be removed but for now allows you to view the admin page as a basic user.




