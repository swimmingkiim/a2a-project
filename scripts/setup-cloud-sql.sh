#!/bin/bash
set -e

# Configuration
REGION="asia-northeast3" # Matching region from deploy_paymaster.sh context (asia-northeast3 in cloudbuild submit command)
INSTANCE_NAME="a2a-paymaster-db"
DB_NAME="paymaster_db"
DB_USER="paymaster_admin"

# Function to check if instance exists
check_instance() {
    gcloud sql instances describe $INSTANCE_NAME --project=$(gcloud config get-value project) &> /dev/null
}

echo "🚀 Setting up Cloud SQL for A2A Paymaster..."

if check_instance; then
    echo "✅ Cloud SQL instance '$INSTANCE_NAME' already exists."
else
    echo "Creating Cloud SQL instance '$INSTANCE_NAME' in '$REGION'..."
    # Micro instance as requested, with auto storage increase
    gcloud sql instances create $INSTANCE_NAME \
        --database-version=POSTGRES_15 \
        --tier=db-f1-micro \
        --region=$REGION \
        --storage-auto-increase \
        --root-password=$(openssl rand -hex 16) # Temporary root password
    
    echo "✅ Instance created."
fi

# Create Database if not exists
echo "Checking database '$DB_NAME'..."
if ! gcloud sql databases list --instance=$INSTANCE_NAME | grep -q $DB_NAME; then
    echo "Creating database '$DB_NAME'..."
    gcloud sql databases create $DB_NAME --instance=$INSTANCE_NAME
    echo "✅ Database created."
else
    echo "✅ Database '$DB_NAME' already exists."
fi

# Create User if not exists
echo "Checking user '$DB_USER'..."
if ! gcloud sql users list --instance=$INSTANCE_NAME | grep -q $DB_USER; then
    echo "Creating user '$DB_USER'..."
    generated_password=$(openssl rand -hex 16)
    gcloud sql users create $DB_USER \
        --instance=$INSTANCE_NAME \
        --password=$generated_password

    echo "✅ User created."
    echo ""
    echo "⚠️  IMPORTANT: SAVE THESE CREDENTIALS!"
    echo "User: $DB_USER"
    echo "Password: $generated_password"
    echo "Connection Name: $(gcloud sql instances describe $INSTANCE_NAME --format='value(connectionName)')"
    echo ""
    
    # Store password in Secret Manager
    echo -n "$generated_password" | gcloud secrets create DB_PASSWORD --data-file=- --replication-policy="automatic" || \
    echo -n "$generated_password" | gcloud secrets versions add DB_PASSWORD --data-file=-
    echo "🔐 Password saved to Secret Manager (DB_PASSWORD)."
else
    echo "✅ User '$DB_USER' already exists."
fi

echo "🎉 Cloud SQL Setup Complete!"
