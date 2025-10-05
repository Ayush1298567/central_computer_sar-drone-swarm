#!/bin/bash
# SAR Drone System - Production Deployment Script

set -euo pipefail

# Configuration
NAMESPACE="sar-drone-system"
ENVIRONMENT="${ENVIRONMENT:-production}"
DRY_RUN="${DRY_RUN:-false}"
SKIP_TESTS="${SKIP_TESTS:-false}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check prerequisites
check_prerequisites() {
    log_info "Checking prerequisites..."
    
    # Check if kubectl is installed
    if ! command -v kubectl &> /dev/null; then
        log_error "kubectl is not installed"
        exit 1
    fi
    
    # Check if helm is installed
    if ! command -v helm &> /dev/null; then
        log_error "helm is not installed"
        exit 1
    fi
    
    # Check if docker is installed
    if ! command -v docker &> /dev/null; then
        log_error "docker is not installed"
        exit 1
    fi
    
    # Check cluster connectivity
    if ! kubectl cluster-info &> /dev/null; then
        log_error "Cannot connect to Kubernetes cluster"
        exit 1
    fi
    
    log_success "Prerequisites check passed"
}

# Build and push Docker images
build_images() {
    log_info "Building Docker images..."
    
    # Build backend image
    docker build -t sar-drone/backend:latest -f backend/Dockerfile.production backend/
    docker tag sar-drone/backend:latest sar-drone/backend:${ENVIRONMENT}
    
    # Build frontend image
    docker build -t sar-drone/frontend:latest -f frontend/Dockerfile frontend/
    docker tag sar-drone/frontend:latest sar-drone/frontend:${ENVIRONMENT}
    
    log_success "Docker images built successfully"
}

# Run tests
run_tests() {
    if [[ "$SKIP_TESTS" == "true" ]]; then
        log_warning "Skipping tests"
        return
    fi
    
    log_info "Running tests..."
    
    # Run backend tests
    cd backend
    python -m pytest tests/ -v --cov=app --cov-report=html
    cd ..
    
    # Run frontend tests
    cd frontend
    npm test -- --coverage --watchAll=false
    cd ..
    
    log_success "All tests passed"
}

# Deploy to Kubernetes
deploy_kubernetes() {
    log_info "Deploying to Kubernetes..."
    
    # Create namespace
    kubectl apply -f deployment/kubernetes/namespace.yaml
    
    # Create secrets
    kubectl create secret generic sar-secrets \
        --from-literal=database-url="$DATABASE_URL" \
        --from-literal=redis-url="$REDIS_URL" \
        --from-literal=secret-key="$SECRET_KEY" \
        --from-literal=grafana-password="$GRAFANA_PASSWORD" \
        --namespace=$NAMESPACE \
        --dry-run=client -o yaml | kubectl apply -f -
    
    # Deploy backend
    kubectl apply -f deployment/kubernetes/backend-deployment.yaml
    
    # Deploy monitoring
    kubectl apply -f deployment/kubernetes/monitoring.yaml
    
    # Deploy ingress
    kubectl apply -f deployment/kubernetes/ingress.yaml
    
    # Wait for deployments to be ready
    kubectl wait --for=condition=available --timeout=300s deployment/sar-backend -n $NAMESPACE
    kubectl wait --for=condition=available --timeout=300s deployment/prometheus -n $NAMESPACE
    kubectl wait --for=condition=available --timeout=300s deployment/grafana -n $NAMESPACE
    
    log_success "Kubernetes deployment completed"
}

# Run database migrations
run_migrations() {
    log_info "Running database migrations..."
    
    # Run migrations using a job
    kubectl apply -f - <<EOF
apiVersion: batch/v1
kind: Job
metadata:
  name: sar-migrations
  namespace: $NAMESPACE
spec:
  template:
    spec:
      containers:
      - name: migrations
        image: sar-drone/backend:latest
        command: ["python", "app/database/migrate.py"]
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: sar-secrets
              key: database-url
      restartPolicy: Never
  backoffLimit: 3
EOF
    
    # Wait for migration job to complete
    kubectl wait --for=condition=complete --timeout=300s job/sar-migrations -n $NAMESPACE
    
    # Clean up the job
    kubectl delete job sar-migrations -n $NAMESPACE
    
    log_success "Database migrations completed"
}

# Health check
health_check() {
    log_info "Performing health check..."
    
    # Get the service endpoint
    SERVICE_IP=$(kubectl get service sar-backend-service -n $NAMESPACE -o jsonpath='{.spec.clusterIP}')
    
    # Check health endpoint
    if kubectl run health-check --rm -i --restart=Never --image=curlimages/curl -- \
        curl -f http://$SERVICE_IP:8000/health; then
        log_success "Health check passed"
    else
        log_error "Health check failed"
        exit 1
    fi
}

# Rollback function
rollback() {
    log_warning "Rolling back deployment..."
    
    # Rollback backend deployment
    kubectl rollout undo deployment/sar-backend -n $NAMESPACE
    
    # Wait for rollback to complete
    kubectl rollout status deployment/sar-backend -n $NAMESPACE
    
    log_success "Rollback completed"
}

# Main deployment function
main() {
    log_info "Starting SAR Drone System deployment to $ENVIRONMENT environment"
    
    # Check if dry run
    if [[ "$DRY_RUN" == "true" ]]; then
        log_warning "DRY RUN MODE - No changes will be made"
    fi
    
    # Pre-deployment checks
    check_prerequisites
    
    # Build and test
    build_images
    run_tests
    
    # Deploy
    if [[ "$DRY_RUN" == "false" ]]; then
        deploy_kubernetes
        run_migrations
        health_check
        
        log_success "Deployment completed successfully!"
        log_info "Access the system at: https://sar-drone.yourdomain.com"
        log_info "Monitor at: https://monitor.sar-drone.yourdomain.com"
    else
        log_info "Dry run completed - no changes made"
    fi
}

# Error handling
trap 'log_error "Deployment failed at line $LINENO"; rollback; exit 1' ERR

# Run main function
main "$@"
