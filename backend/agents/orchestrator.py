# backend/agents/orchestrator.py
from backend.models.signal import NormalizedSignal
from backend.services.firestore_service import firestore_service
from backend.agents.signal_fusion import SignalFusionAgent
from backend.agents.credibility import CredibilityAgent
from backend.agents.classification import ClassificationAgent
from backend.agents.resource_allocation import ResourceAllocationAgent
from backend.agents.simulation import SimulationAgent
from backend.agents.stakeholder_messaging import StakeholderMessagingAgent
from backend.agents.recovery import RecoveryAgent
from backend.models.incident import Incident
from backend.services.websocket_manager import ws_manager

# Initialize our agents
signal_fusion_agent = SignalFusionAgent()
credibility_agent = CredibilityAgent()
classification_agent = ClassificationAgent()
resource_allocation_agent = ResourceAllocationAgent()
simulation_agent = SimulationAgent()
stakeholder_messaging_agent = StakeholderMessagingAgent()
recovery_agent = RecoveryAgent()

class Orchestrator:
    """
    Main controller that runs the agent pipeline.
    Triggered when a new signal arrives.
    """
    
    async def process_signal(self, signal: NormalizedSignal):
        print(f"[Orchestrator] Processing new signal: {signal.signal_id}")
        
        # 1. Fetch active incidents to compare against
        active_incident_dicts = await firestore_service.get_active_incidents()
        active_incidents = [Incident(**d) for d in active_incident_dicts]
        
        # 2. Signal Fusion (Clustering)
        # We pass a dummy incident_id for the run since we don't know it yet
        temp_id = f"inc_candidate_{signal.signal_id[-4:]}"
        context = await signal_fusion_agent.run(
            incident_id=temp_id, 
            input_data={'new_signal': signal, 'active_incidents': active_incidents}
        )
        
        incident_id = context.target_incident_id if not context.is_new_incident else context.cluster_id
        
        # 3. Credibility Scoring
        cred_report = await credibility_agent.run(incident_id=incident_id, input_data=context)
        
        # --- DAY 4 RECOVERY/RETRACTION ---
        if not context.is_new_incident:
            target = next(i for i in active_incidents if i.incident_id == incident_id)
            recovery_output = await recovery_agent.run(
                incident_id=incident_id,
                input_data={'incident': target, 'new_signal': signal}
            )
            if recovery_output['action_type'] == 'RETRACT':
                target.status = 'false_alarm'
                target.pipeline_stage = 'resolved'
                await firestore_service.save_incident(target)
                await ws_manager.broadcast("incident_update", target.model_dump(), "incident")
                print(f"[Orchestrator] Incident {incident_id} retracted as false alarm.")
                return
            elif recovery_output['action_type'] == 'ESCALATE':
                target.status = 'monitoring'
        
        # 4. Classification
        classification = await classification_agent.run(
            incident_id=incident_id, 
            input_data={'context': context, 'credibility': cred_report}
        )
        
        # 5. Persist Incident
        if context.is_new_incident:
            incident = Incident(
                incident_id=incident_id,
                status="detecting" if classification.confidence < 0.6 else "active",
                location={"lat": context.center_location.lat, "lng": context.center_location.lng, "area_name": context.center_location.area_name},
                classification=classification,
                signal_ids=[signal.signal_id],
                signal_count=1,
                pipeline_stage="classified"
            )
        else:
            # Update existing
            # In a real app we would merge signals, for now we just overwrite classification
            target = next(i for i in active_incidents if i.incident_id == incident_id)
            incident = target
            if signal.signal_id not in incident.signal_ids:
                incident.signal_ids.append(signal.signal_id)
                incident.signal_count += 1
            incident.classification = classification
            incident.pipeline_stage = "classified"
            if classification.confidence >= 0.6:
                incident.status = "active"
                
                
        await firestore_service.save_incident(incident)
        
        # --- DAY 3 PIPELINE EXTENSION ---
        if incident.status == "active":
            # 6. Resource Allocation
            resource_state = await firestore_service.get_resource_state()
            allocation_plan = await resource_allocation_agent.run(
                incident_id=incident_id,
                input_data={
                    'incident': incident,
                    'active_incidents': active_incidents + [incident] if context.is_new_incident else active_incidents,
                    'resource_state': resource_state
                }
            )
            
            # 7. Simulation
            simulations = await simulation_agent.run(
                incident_id=incident_id,
                input_data={
                    'incident': incident,
                    'allocation': allocation_plan
                }
            )
            
            # 8. Stakeholder Messaging
            messages = await stakeholder_messaging_agent.run(
                incident_id=incident_id,
                input_data={
                    'incident': incident,
                    'allocation': allocation_plan,
                    'simulation': simulations
                }
            )
            incident.pipeline_stage = "notified"
            await firestore_service.save_incident(incident) # Update stage
        
        # Broadcast the updated incident state to Flutter app
        await ws_manager.broadcast("incident_update", incident.model_dump(), "incident")
        
        print(f"[Orchestrator] Finished pipeline for {incident_id}. State: {incident.status}")

# Singleton orchestrator
orchestrator = Orchestrator()
