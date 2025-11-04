#!/usr/bin/env python3
"""
Fix AI code to work with existing database structure
"""

import os
import re

def fix_aurea_intelligence():
    """Fix aurea_intelligence.py to work with existing DB"""
    file_path = "aurea_intelligence.py"
    
    if not os.path.exists(file_path):
        print(f"File {file_path} not found")
        return
    
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Fix the AUREAConsciousness model to match actual DB
    # The table has an integer ID and session_id, not UUID
    old_model = """class AUREAConsciousness(Base):
    __tablename__ = "aurea_consciousness"
    
    id = Column(Integer, primary_key=True)"""
    
    new_model = """class AUREAConsciousness(Base):
    __tablename__ = "aurea_consciousness"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String(255), nullable=True)"""
    
    if old_model in content:
        content = content.replace(old_model, new_model)
        print("Fixed AUREAConsciousness model")
    
    # Fix any UUID references to Integer for aurea_consciousness
    content = re.sub(
        r'consciousness_id = Column\(String.*?\)',
        'consciousness_id = Column(Integer)',
        content
    )
    
    with open(file_path, 'w') as f:
        f.write(content)
    
    print(f"Fixed {file_path}")

def fix_ai_board():
    """Fix ai_board.py to work with existing DB"""
    file_path = "ai_board.py"
    
    if not os.path.exists(file_path):
        print(f"File {file_path} not found")
        return
    
    with open(file_path, 'r') as f:
        content = f.read()
    
    # The ai_board_sessions table has session_id column
    # Make sure we're using it properly
    content = re.sub(
        r'session_id = Column\(String.*?, unique=True\)',
        'session_id = Column(String(255), unique=True)',
        content
    )
    
    with open(file_path, 'w') as f:
        f.write(content)
    
    print(f"Fixed {file_path}")

def main():
    print("Fixing AI code to work with database...")
    fix_aurea_intelligence()
    fix_ai_board()
    print("Done! Ready to rebuild and deploy.")

if __name__ == "__main__":
    main()