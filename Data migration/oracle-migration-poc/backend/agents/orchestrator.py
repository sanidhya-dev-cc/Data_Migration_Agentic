"""
LangGraph Migration Orchestrator
Main orchestration graph for migration workflow
"""

from typing import TypedDict, Annotated, List, Dict, Any
from langgraph.graph import StateGraph, END
from langchain_openai import AzureChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
import structlog
import os
from datetime import datetime

from models.migration import (
    MigrationRequest, MigrationStatus, MigrationStep,
    MigrationPlan, AgentLog, ValidationResult
)

logger = structlog.get_logger(__name__)


class MigrationState(TypedDict):
    """State for migration orchestration"""
    migration_id: str
    request: Dict[str, Any]
    status: str
    current_step: str
    schema_analysis: Dict[str, Any]
    migration_plan: Dict[str, Any]
    execution_result: Dict[str, Any]
    validation_result: Dict[str, Any]
    agent_logs: List[Dict[str, Any]]
    error: str
    requires_approval: bool
    approved: bool


class MigrationOrchestrator:
    """Main orchestrator for migration workflow using LangGraph"""
    
    def __init__(self):
        self.llm = self._initialize_llm()
        self.graph = self._build_graph()
        
    def _initialize_llm(self) -> AzureChatOpenAI:
        """Initialize Azure OpenAI LLM"""
        return AzureChatOpenAI(
            azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
            api_key=os.getenv("AZURE_OPENAI_API_KEY"),
            api_version=os.getenv("AZURE_OPENAI_API_VERSION"),
            deployment_name=os.getenv("AZURE_OPENAI_DEPLOYMENT"),
            temperature=0.3
        )
    
    def _build_graph(self) -> StateGraph:
        """Build the LangGraph orchestration graph"""
        workflow = StateGraph(MigrationState)
        
        # Add nodes
        workflow.add_node("intent_analyzer", self.analyze_intent)
        workflow.add_node("schema_discovery", self.discover_schema)
        workflow.add_node("dependency_analyzer", self.analyze_dependencies)
        workflow.add_node("migration_planner", self.plan_migration)
        workflow.add_node("await_approval", self.await_approval)
        workflow.add_node("migration_executor", self.execute_migration)
        workflow.add_node("validator", self.validate_migration)
        workflow.add_node("reconciliation", self.reconcile_issues)
        workflow.add_node("complete", self.complete_migration)
        workflow.add_node("error_handler", self.handle_error)
        
        # Define edges
        workflow.set_entry_point("intent_analyzer")
        workflow.add_edge("intent_analyzer", "schema_discovery")
        workflow.add_edge("schema_discovery", "dependency_analyzer")
        workflow.add_edge("dependency_analyzer", "migration_planner")
        workflow.add_edge("migration_planner", "await_approval")
        
        # Conditional edges from approval
        workflow.add_conditional_edges(
            "await_approval",
            self.check_approval,
            {
                "approved": "migration_executor",
                "rejected": "error_handler",
                "waiting": "await_approval"
            }
        )
        
        workflow.add_edge("migration_executor", "validator")
        
        # Conditional edges from validation
        workflow.add_conditional_edges(
            "validator",
            self.check_validation,
            {
                "passed": "complete",
                "failed": "reconciliation",
                "error": "error_handler"
            }
        )
        
        workflow.add_conditional_edges(
            "reconciliation",
            self.check_reconciliation,
            {
                "retry": "migration_executor",
                "abort": "error_handler",
                "manual": "await_approval"
            }
        )
        
        workflow.add_edge("complete", END)
        workflow.add_edge("error_handler", END)
        
        return workflow.compile()
    
    def analyze_intent(self, state: MigrationState) -> MigrationState:
        """Analyze migration intent using LLM"""
        logger.info(f"Analyzing intent for migration {state['migration_id']}")
        
        request = state["request"]
        
        system_msg = SystemMessage(content="""You are an expert Oracle database migration analyst.
Analyze the migration request and extract key information:
- Migration type (two-step: 19c standalone → 19c PDB → 23c PDB)
- Business priority and risk tolerance
- Downtime constraints
- Critical dependencies

Provide a structured analysis in JSON format.""")
        
        user_msg = HumanMessage(content=f"""Analyze this migration request:
Migration Name: {request.get('migration_name')}
Source: {request.get('source_db', {}).get('db_type')}
Target: {request.get('target_db', {}).get('db_type')}
Tables: {len(request.get('tables', []))}
Priority: {request.get('business_priority')}
Max Downtime: {request.get('max_downtime_minutes')} minutes

Provide analysis.""")
        
        try:
            response = self.llm.invoke([system_msg, user_msg])
            
            state["agent_logs"].append({
                "timestamp": datetime.utcnow().isoformat(),
                "agent_name": "Intent Analyzer",
                "action": "analyze_intent",
                "reasoning": response.content,
                "metadata": {}
            })
            
            state["status"] = MigrationStatus.ANALYZING.value
            logger.info(f"Intent analysis completed for {state['migration_id']}")
            
        except Exception as e:
            logger.error(f"Intent analysis failed: {str(e)}")
            state["error"] = f"Intent analysis failed: {str(e)}"
            state["status"] = MigrationStatus.FAILED.value
        
        return state
    
    def discover_schema(self, state: MigrationState) -> MigrationState:
        """Discover source schema (metadata only, no sensitive data)"""
        logger.info(f"Discovering schema for migration {state['migration_id']}")
        
        try:
            # In production, this would call OracleClient
            # For POC, we use mock data
            from db import get_mock_tables
            
            tables = get_mock_tables()
            
            state["schema_analysis"] = {
                "total_tables": len(tables),
                "total_size_mb": sum(t.size_mb for t in tables),
                "total_rows": sum(t.row_count for t in tables),
                "tables": [t.dict() for t in tables]
            }
            
            state["agent_logs"].append({
                "timestamp": datetime.utcnow().isoformat(),
                "agent_name": "Schema Discovery",
                "action": "discover_schema",
                "reasoning": f"Discovered {len(tables)} tables with total size {sum(t.size_mb for t in tables):.2f} MB",
                "metadata": state["schema_analysis"]
            })
            
            logger.info(f"Schema discovery completed: {len(tables)} tables found")
            
        except Exception as e:
            logger.error(f"Schema discovery failed: {str(e)}")
            state["error"] = f"Schema discovery failed: {str(e)}"
            state["status"] = MigrationStatus.FAILED.value
        
        return state
    
    def analyze_dependencies(self, state: MigrationState) -> MigrationState:
        """Analyze table dependencies using LLM"""
        logger.info(f"Analyzing dependencies for migration {state['migration_id']}")
        
        try:
            from db import get_mock_dependencies
            
            dependencies = get_mock_dependencies()
            
            # Use LLM to analyze dependency risk
            system_msg = SystemMessage(content="""You are an Oracle database dependency expert.
Analyze table dependencies and determine migration order to avoid constraint violations.
Consider foreign keys, views, triggers, and materialized views.""")
            
            dep_description = "\n".join([
                f"- {d.table_name} depends on: {', '.join(d.depends_on)} ({d.dependency_type})"
                for d in dependencies
            ])
            
            user_msg = HumanMessage(content=f"""Analyze these dependencies and determine optimal migration order:
            
{dep_description}

Provide:
1. Recommended migration order
2. Risk assessment
3. Critical dependencies that require special handling""")
            
            response = self.llm.invoke([system_msg, user_msg])
            
            state["schema_analysis"]["dependencies"] = [d.dict() for d in dependencies]
            state["schema_analysis"]["dependency_analysis"] = response.content
            
            state["agent_logs"].append({
                "timestamp": datetime.utcnow().isoformat(),
                "agent_name": "Dependency Analyzer",
                "action": "analyze_dependencies",
                "reasoning": response.content,
                "metadata": {"dependencies": len(dependencies)}
            })
            
            logger.info(f"Dependency analysis completed: {len(dependencies)} dependencies found")
            
        except Exception as e:
            logger.error(f"Dependency analysis failed: {str(e)}")
            state["error"] = f"Dependency analysis failed: {str(e)}"
        
        return state
    
    def plan_migration(self, state: MigrationState) -> MigrationState:
        """Generate migration plan using LLM"""
        logger.info(f"Planning migration for {state['migration_id']}")
        
        state["status"] = MigrationStatus.PLANNING.value
        
        try:
            schema = state.get("schema_analysis", {})
            request = state["request"]
            
            system_msg = SystemMessage(content="""You are an expert Oracle migration planner.
Create a detailed two-step migration plan:

Step 1: Convert Oracle 19c standalone (non-CDB) to Oracle 19c PDB
Step 2: Migrate Oracle 19c PDB to Oracle 23c PDB

Consider:
- Table dependencies and execution order
- Pre-migration checks (backups, storage, compatibility)
- Risk mitigation strategies
- Rollback procedures
- Post-migration validation

Provide a structured plan.""")
            
            user_msg = HumanMessage(content=f"""Create migration plan for:

Source: Oracle 19c standalone
Intermediate: Oracle 19c CDB/PDB
Target: Oracle 23c CDB/PDB

Tables: {schema.get('total_tables')}
Total Size: {schema.get('total_size_mb')} MB
Total Rows: {schema.get('total_rows')}

Dependencies:
{schema.get('dependency_analysis', 'None')}

Business Priority: {request.get('business_priority')}
Max Downtime: {request.get('max_downtime_minutes')} minutes

Generate comprehensive migration plan.""")
            
            response = self.llm.invoke([system_msg, user_msg])
            
            # Create structured plan
            state["migration_plan"] = {
                "plan_id": f"PLAN-{state['migration_id']}",
                "step_1": {
                    "step": "non_cdb_to_pdb",
                    "execution_order": ["CUSTOMER", "PRODUCTS", "ORDERS", "ORDER_ITEMS", "PAYMENTS"],
                    "estimated_duration_minutes": 30,
                    "risk_level": "medium"
                },
                "step_2": {
                    "step": "pdb_19c_to_23c",
                    "execution_order": ["CUSTOMER", "PRODUCTS", "ORDERS", "ORDER_ITEMS", "PAYMENTS"],
                    "estimated_duration_minutes": 45,
                    "risk_level": "low"
                },
                "ai_reasoning": response.content,
                "pre_checks": [
                    "Verify source database backup",
                    "Validate target storage capacity",
                    "Check Oracle compatibility",
                    "Confirm network connectivity"
                ],
                "post_checks": [
                    "Validate row counts",
                    "Verify constraints and indexes",
                    "Test database links",
                    "Validate application connectivity"
                ]
            }
            
            state["requires_approval"] = True
            state["status"] = MigrationStatus.AWAITING_APPROVAL.value
            
            state["agent_logs"].append({
                "timestamp": datetime.utcnow().isoformat(),
                "agent_name": "Migration Planner",
                "action": "plan_migration",
                "reasoning": response.content,
                "metadata": state["migration_plan"]
            })
            
            logger.info(f"Migration plan created for {state['migration_id']}")
            
        except Exception as e:
            logger.error(f"Migration planning failed: {str(e)}")
            state["error"] = f"Migration planning failed: {str(e)}"
            state["status"] = MigrationStatus.FAILED.value
        
        return state
    
    def await_approval(self, state: MigrationState) -> MigrationState:
        """Wait for human approval"""
        logger.info(f"Awaiting approval for migration {state['migration_id']}")
        # This is a holding state - approval comes from external API call
        return state
    
    def check_approval(self, state: MigrationState) -> str:
        """Check if migration is approved"""
        if state.get("approved"):
            return "approved"
        elif state.get("error"):
            return "rejected"
        return "waiting"
    
    def execute_migration(self, state: MigrationState) -> MigrationState:
        """Execute migration (controlled Python, not LLM-generated SQL)"""
        logger.info(f"Executing migration for {state['migration_id']}")
        
        state["status"] = MigrationStatus.EXECUTING.value
        
        try:
            # In production, this would execute actual migration
            # For POC, we simulate execution
            plan = state.get("migration_plan", {})
            
            state["execution_result"] = {
                "step_1_completed": True,
                "step_2_completed": True,
                "tables_migrated": plan.get("step_1", {}).get("execution_order", []),
                "execution_time_minutes": 75,
                "errors": []
            }
            
            state["agent_logs"].append({
                "timestamp": datetime.utcnow().isoformat(),
                "agent_name": "Migration Executor",
                "action": "execute_migration",
                "reasoning": "Migration executed successfully using controlled Python execution (not LLM-generated SQL)",
                "metadata": state["execution_result"]
            })
            
            logger.info(f"Migration execution completed for {state['migration_id']}")
            
        except Exception as e:
            logger.error(f"Migration execution failed: {str(e)}")
            state["error"] = f"Migration execution failed: {str(e)}"
            state["status"] = MigrationStatus.FAILED.value
        
        return state
    
    def validate_migration(self, state: MigrationState) -> MigrationState:
        """Validate migration results"""
        logger.info(f"Validating migration for {state['migration_id']}")
        
        state["status"] = MigrationStatus.VALIDATING.value
        
        try:
            # Simulate validation
            state["validation_result"] = {
                "passed": True,
                "source_row_count": 1650000,
                "target_row_count": 1650000,
                "row_count_match": True,
                "schema_match": True,
                "constraint_match": True,
                "index_match": True,
                "issues": []
            }
            
            state["agent_logs"].append({
                "timestamp": datetime.utcnow().isoformat(),
                "agent_name": "Validator",
                "action": "validate_migration",
                "reasoning": "All validation checks passed successfully",
                "metadata": state["validation_result"]
            })
            
            logger.info(f"Validation completed for {state['migration_id']}")
            
        except Exception as e:
            logger.error(f"Validation failed: {str(e)}")
            state["error"] = f"Validation failed: {str(e)}"
        
        return state
    
    def check_validation(self, state: MigrationState) -> str:
        """Check validation result"""
        validation = state.get("validation_result", {})
        if validation.get("passed"):
            return "passed"
        elif state.get("error"):
            return "error"
        return "failed"
    
    def reconcile_issues(self, state: MigrationState) -> MigrationState:
        """Attempt to reconcile validation issues"""
        logger.info(f"Reconciling issues for migration {state['migration_id']}")
        
        # LLM analyzes issues and recommends repair strategy
        # This is where the "self-healing" capability shines
        
        return state
    
    def check_reconciliation(self, state: MigrationState) -> str:
        """Check reconciliation result"""
        # Simplified for POC
        return "retry"
    
    def complete_migration(self, state: MigrationState) -> MigrationState:
        """Complete migration"""
        logger.info(f"Completing migration {state['migration_id']}")
        
        state["status"] = MigrationStatus.COMPLETED.value
        
        state["agent_logs"].append({
            "timestamp": datetime.utcnow().isoformat(),
            "agent_name": "Migration Orchestrator",
            "action": "complete_migration",
            "reasoning": "Migration completed successfully with all validations passed",
            "metadata": {}
        })
        
        return state
    
    def handle_error(self, state: MigrationState) -> MigrationState:
        """Handle migration error"""
        logger.error(f"Migration failed: {state.get('error')}")
        
        state["status"] = MigrationStatus.FAILED.value
        
        return state
    
    async def start_migration(self, request: MigrationRequest) -> str:
        """Start migration workflow"""
        import uuid
        
        migration_id = str(uuid.uuid4())
        
        initial_state: MigrationState = {
            "migration_id": migration_id,
            "request": request.dict(),
            "status": MigrationStatus.PENDING.value,
            "current_step": "intent_analyzer",
            "schema_analysis": {},
            "migration_plan": {},
            "execution_result": {},
            "validation_result": {},
            "agent_logs": [],
            "error": "",
            "requires_approval": False,
            "approved": False
        }
        
        # Execute graph
        result = self.graph.invoke(initial_state)
        
        return migration_id
