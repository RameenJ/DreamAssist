#!/usr/bin/env python3
"""Test script to verify persona unlock logic"""

from models.persona_schemas import PERSONA_DEFINITIONS

# Test all personas
for persona_id, persona_data in PERSONA_DEFINITIONS.items():
    unlocked = []  # Simulating no user-specific unlocks
    
    is_unlocked = (
        persona_id in unlocked or 
        persona_id == "newton" or
        persona_data.get("unlock_condition") == "Always unlocked"
    )
    
    print(f"\n{'='*50}")
    print(f"Persona: {persona_id}")
    print(f"Name: {persona_data['name']}")
    print(f"Unlock condition: {persona_data.get('unlock_condition')}")
    print(f"Is unlocked: {is_unlocked}")
    print(f"Unlock condition check: {persona_data.get('unlock_condition') == 'Always unlocked'}")
    print(f"Default check (newton): {persona_id == 'newton'}")
