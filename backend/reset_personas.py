#!/usr/bin/env python3
"""Reset personas collection with updated unlock_condition"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from models.persona_schemas import PERSONA_DEFINITIONS
from datetime import datetime

async def reset_personas():
    """Delete and reinitialize personas collection"""
    try:
        # Connect to MongoDB
        client = AsyncIOMotorClient('mongodb://localhost:27017')
        db = client.dream_assist
        personas_collection = db.personas
        
        # Delete all personas
        result = await personas_collection.delete_many({})
        print(f'✅ Deleted {result.deleted_count} personas')
        
        # Reinitialize with new data
        for persona_id, persona_data in PERSONA_DEFINITIONS.items():
            await personas_collection.insert_one({
                '_id': persona_id,
                **persona_data,
                'created_at': datetime.utcnow(),
                'is_default': persona_id == 'newton'
            })
            print(f'✅ Initialized {persona_id}: unlock_condition="{persona_data.get("unlock_condition")}"')
        
        print('\n✅ Personas reinitialized successfully!')
        print('   - Einstein: Always unlocked')
        print('   - Newton: Always unlocked')
        print('   - Marie Curie: Score 80%+ on a quiz')
        
        client.close()
    except Exception as e:
        print(f'❌ Error: {str(e)}')
        sys.exit(1)

if __name__ == '__main__':
    asyncio.run(reset_personas())
