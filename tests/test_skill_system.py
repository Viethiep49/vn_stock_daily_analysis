import pytest
from src.agents.skills.registry import list_skills, get_skill_content
from src.agents.skill_agent import SkillAgent
from src.agents.protocols import AgentContext

def test_list_skills():
    skills = list_skills()
    assert "VSA" in skills
    assert "CANSLIM" in skills
    assert len(skills) >= 2

def test_get_skill_content():
    vsa_content = get_skill_content("VSA")
    assert "# Volume Spread Analysis" in vsa_content
    assert "Accumulation" in vsa_content

    canslim_content = get_skill_content("CANSLIM")
    assert "# CANSLIM Analysis" in canslim_content
    assert "Current Quarterly Earnings" in canslim_content

def test_skill_agent_init():
    context = AgentContext(symbol="HPG")
    agent = SkillAgent(skill_name="VSA")
    
    assert agent.skill_name == "VSA"
    assert "Volume Spread Analysis" in agent.skill_content
    
    system_prompt = agent.system_prompt(context)
    assert "VSA methodology" in system_prompt
    assert "YOUR SPECIALIZED PLAYBOOK" in system_prompt
    assert "Volume Spread Analysis" in system_prompt
    
    user_prompt = agent.user_prompt(context)
    assert "VSA analysis for HPG" in user_prompt

def test_invalid_skill():
    with pytest.raises(FileNotFoundError):
        get_skill_content("NON_EXISTENT_SKILL")
