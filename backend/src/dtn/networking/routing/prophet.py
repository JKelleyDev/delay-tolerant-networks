"""
PRoPHET Routing Algorithm

Implements Probabilistic Routing Protocol using History of Encounters and Transitivity
for Delay Tolerant Networks. Uses delivery predictability based on encounter history.
"""

from typing import List, Dict, Tuple
from datetime import datetime, timedelta
import math

from .base_router import BaseRouter, RoutingDecision
from ...core.bundle import Bundle
from ...orbital.contact_prediction import ContactWindow


class ProphetRouter(BaseRouter):
    """
    PRoPHET (Probabilistic Routing Protocol using History of Encounters and Transitivity)
    
    Maintains delivery predictability values for each destination based on:
    - Direct encounter history
    - Transitivity (if A meets B often and B meets C often, A can deliver to C via B)
    - Aging (predictability decreases over time without encounters)
    """
    
    def __init__(self, node_id: str, buffer_size: int = 10 * 1024 * 1024):
        super().__init__(node_id, buffer_size)
        
        # PRoPHET parameters (from RFC 6693)
        self.p_init = 0.75  # Initial predictability when first encountered
        self.p_encounter_max = 0.7  # Maximum predictability for encounters
        self.beta = 0.9  # Scaling factor for encounter predictability
        self.gamma = 0.95  # Scaling factor for transitivity
        self.delta = 0.01  # Aging constant
        self.aging_interval = timedelta(minutes=1)  # How often to age predictabilities
        
        # PRoPHET state
        self.delivery_predictability: Dict[str, float] = {}  # destination -> predictability
        self.last_encounter: Dict[str, datetime] = {}  # node -> last encounter time
        self.last_aging = datetime.now()
        
        # Transitive information exchange
        self.neighbor_predictabilities: Dict[str, Dict[str, float]] = {}  # neighbor -> {dest -> pred}
    
    def should_forward(
        self, 
        bundle: Bundle, 
        available_contacts: List[ContactWindow],
        current_time: datetime
    ) -> RoutingDecision:
        """
        PRoPHET forwarding decision based on delivery predictability.
        """
        if not available_contacts:
            return RoutingDecision(
                action="store",
                reason="No contacts available"
            )
        
        destination = bundle.destination.ssp
        my_predictability = self.delivery_predictability.get(destination, 0.0)
        
        # Find neighbor with higher predictability
        best_contact = None
        best_predictability = my_predictability
        best_node = None
        
        for contact in available_contacts:
            # Determine neighbor node
            neighbor = None
            if contact.source_id == self.node_id:
                neighbor = contact.target_id
            elif contact.target_id == self.node_id:
                neighbor = contact.source_id
            else:
                continue
            
            # Get neighbor's predictability for destination
            neighbor_pred = self._get_neighbor_predictability(neighbor, destination)
            
            # Forward only if neighbor has significantly higher predictability
            threshold = my_predictability + 0.1  # Require meaningful improvement
            
            if neighbor_pred > threshold and neighbor_pred > best_predictability:
                best_predictability = neighbor_pred
                best_contact = contact
                best_node = neighbor
        
        if best_contact and best_node:
            return RoutingDecision(
                action="forward",
                next_hop=best_node,
                reason=f"Higher predictability: {best_predictability:.3f} > {my_predictability:.3f}",
                priority=best_predictability,
                contact_window=best_contact
            )
        
        # Check if we have reasonable predictability for direct delivery
        if destination in self.neighbor_nodes and my_predictability > 0.5:
            direct_contact = self.get_contact_to_node(destination)
            if direct_contact:
                return RoutingDecision(
                    action="forward",
                    next_hop=destination,
                    reason=f"Direct delivery (predictability: {my_predictability:.3f})",
                    priority=my_predictability + 1.0,  # Boost for direct delivery
                    contact_window=direct_contact
                )
        
        return RoutingDecision(
            action="store",
            reason=f"No better forwarding options (my pred: {my_predictability:.3f})"
        )
    
    def _get_neighbor_predictability(self, neighbor: str, destination: str) -> float:
        """Get neighbor's predictability for a destination."""
        if neighbor in self.neighbor_predictabilities:
            return self.neighbor_predictabilities[neighbor].get(destination, 0.0)
        return 0.0
    
    def update_routing_info(
        self, 
        contact_plan: List[ContactWindow],
        current_time: datetime
    ):
        """
        Update PRoPHET routing information with new contacts.
        """
        # Age predictabilities if enough time has passed
        if current_time - self.last_aging >= self.aging_interval:
            self._age_predictabilities(current_time)
            self.last_aging = current_time
        
        # Update predictabilities based on current contacts
        current_neighbors = set()
        for contact in contact_plan:
            if contact.start_time <= current_time <= contact.end_time:
                if contact.source_id == self.node_id:
                    neighbor = contact.target_id
                elif contact.target_id == self.node_id:
                    neighbor = contact.source_id
                else:
                    continue
                
                current_neighbors.add(neighbor)
                self._update_encounter_predictability(neighbor, current_time)
        
        # Update transitivity with current neighbors
        self._update_transitive_predictability(current_neighbors)
    
    def _update_encounter_predictability(self, neighbor: str, encounter_time: datetime):
        """Update predictability based on encounter with neighbor."""
        # Update encounter time
        self.last_encounter[neighbor] = encounter_time
        
        # Calculate new predictability
        old_pred = self.delivery_predictability.get(neighbor, 0.0)
        
        if old_pred == 0.0:
            # First encounter
            new_pred = self.p_init
        else:
            # Subsequent encounter - equation from PRoPHET spec
            new_pred = old_pred + (1 - old_pred) * self.p_encounter_max
        
        self.delivery_predictability[neighbor] = min(1.0, new_pred)
        
        self.logger.debug(
            f"Updated predictability for {neighbor}: {old_pred:.3f} -> {new_pred:.3f}"
        )
    
    def _update_transitive_predictability(self, current_neighbors: set):
        """Update predictabilities using transitivity."""
        # Exchange predictability information with neighbors
        for neighbor in current_neighbors:
            # In a real implementation, this would involve message exchange
            # For simulation, we'll use simplified transitivity calculation
            
            neighbor_preds = self.neighbor_predictabilities.get(neighbor, {})
            
            for destination, neighbor_pred in neighbor_preds.items():
                if destination == self.node_id:
                    continue  # Skip self
                
                # Calculate transitive predictability
                my_to_neighbor = self.delivery_predictability.get(neighbor, 0.0)
                neighbor_to_dest = neighbor_pred
                
                transitive_pred = my_to_neighbor * neighbor_to_dest * self.gamma
                
                # Update if transitive path is better
                current_pred = self.delivery_predictability.get(destination, 0.0)
                if transitive_pred > current_pred:
                    self.delivery_predictability[destination] = transitive_pred
                    self.logger.debug(
                        f"Transitive update for {destination} via {neighbor}: "
                        f"{current_pred:.3f} -> {transitive_pred:.3f}"
                    )
    
    def _age_predictabilities(self, current_time: datetime):
        """Age all predictabilities based on time since last encounter."""
        aged_nodes = []
        
        for node, predictability in list(self.delivery_predictability.items()):
            last_encounter = self.last_encounter.get(node, current_time)
            time_since_encounter = (current_time - last_encounter).total_seconds()
            
            # Aging function: P = P * γ^k where k is time units since last encounter
            k = time_since_encounter / self.aging_interval.total_seconds()
            aging_factor = self.gamma ** k
            
            new_pred = predictability * aging_factor
            
            # Remove very low predictabilities to save memory
            if new_pred < 0.01:
                aged_nodes.append(node)
            else:
                self.delivery_predictability[node] = new_pred
        
        # Clean up aged-out predictabilities
        for node in aged_nodes:
            del self.delivery_predictability[node]
            if node in self.last_encounter:
                del self.last_encounter[node]
        
        if aged_nodes:
            self.logger.debug(f"Aged out predictabilities for {len(aged_nodes)} nodes")
    
    def exchange_summary_vector(self, neighbor: str, neighbor_predictabilities: Dict[str, float]):
        """
        Exchange summary vector with neighbor (called during contact).
        """
        # Store neighbor's predictabilities for transitivity calculations
        self.neighbor_predictabilities[neighbor] = neighbor_predictabilities.copy()
        
        # Return our predictabilities for the neighbor
        return self.delivery_predictability.copy()
    
    def calculate_delivery_probability(
        self, 
        destination: str,
        current_time: datetime
    ) -> float:
        """Calculate probability of successful delivery to destination."""
        return self.delivery_predictability.get(destination, 0.0)
    
    def get_algorithm_specific_metrics(self) -> Dict[str, any]:
        """Get PRoPHET-specific performance metrics."""
        base_metrics = self.get_metrics()
        
        prophet_metrics = {
            'algorithm': 'prophet',
            'predictability_entries': len(self.delivery_predictability),
            'average_predictability': 0.0,
            'max_predictability': 0.0,
            'neighbor_info_entries': sum(
                len(preds) for preds in self.neighbor_predictabilities.values()
            )
        }
        
        if self.delivery_predictability:
            predictabilities = list(self.delivery_predictability.values())
            prophet_metrics['average_predictability'] = sum(predictabilities) / len(predictabilities)
            prophet_metrics['max_predictability'] = max(predictabilities)
        
        return {**base_metrics, **prophet_metrics}
    
    def get_predictability_table(self) -> Dict[str, float]:
        """Get current delivery predictability table."""
        return self.delivery_predictability.copy()
    
    def optimize_buffer(self, current_time: datetime):
        """
        Optimize buffer usage by removing bundles with low delivery probability.
        """
        if self.get_buffer_utilization() < 90:
            return
        
        bundles = self.get_stored_bundles()
        if not bundles:
            return
        
        # Sort bundles by delivery probability (ascending)
        def delivery_prob_score(bundle: Bundle) -> float:
            destination = bundle.destination.ssp
            pred = self.delivery_predictability.get(destination, 0.0)
            
            # Consider remaining lifetime
            remaining_hours = bundle.remaining_lifetime.total_seconds() / 3600
            if remaining_hours <= 0:
                return -1.0  # Expired bundles first
            
            # Lower score = more likely to be dropped
            return pred * remaining_hours
        
        bundles.sort(key=delivery_prob_score)
        
        # Remove bundles with lowest delivery probability (bottom 25%)
        to_remove = max(1, len(bundles) // 4)
        
        for bundle in bundles[:to_remove]:
            dest = bundle.destination.ssp
            pred = self.delivery_predictability.get(dest, 0.0)
            self.remove_bundle(bundle.bundle_id)
            self.logger.debug(
                f"Removed low-probability bundle {bundle.bundle_id} "
                f"(dest: {dest}, pred: {pred:.3f})"
            )
    
    def __str__(self) -> str:
        return f"ProphetRouter({self.node_id}, preds={len(self.delivery_predictability)})"