# FYP Health App - Backend Architecture & LangGraph Guide

This document explains the "Agentic" architecture of the backend, specifically focusing on how LangGraph works in this project.

## 1. What is LangGraph?
While LangChain is great for simple prompt chains, **LangGraph** is designed for complex, cyclic, agentic workflows. Instead of a simple "start-to-end" script, LangGraph models your app as a **State Machine (Graph)**. 
- It can loop back on itself.
- It can pause to ask for human permission.
- It maintains "State" (memory) across the entire conversation.

## 2. The Core Concepts in our App

### State (`backend/agent/state.py`)
The State is a dictionary or Pydantic model that gets passed around between every step (Node). Every time a Node runs, it returns an update to this state. 
*In our app, the state holds the patient's vitals, the OCR text from their prescription, and the list of chat messages.*

### Nodes (`backend/agent/nodes/`)
Nodes are just Python functions. They take the current `State`, do some work, and return an updated `State`.
- **`ocr_node`**: Reads an uploaded image and adds the extracted text to the State.
- **`retrieval_node`**: Takes the patient's symptoms from the State, queries the ChromaDB (Vector DB), and adds medical guidelines to the State.
- **`chatbot_node`**: The core LLM (Groq). It looks at the whole State and decides: *Should I answer the user directly, or should I use a tool first?*

### Tools (`backend/agent/tools/`)
Tools are Python functions decorated with `@tool`. We bind these tools to the LLM. When the LLM realizes it needs to find a hospital, it doesn't try to guess; it generates a "Tool Call".

### Edges and Conditional Routing (`backend/agent/graph.py`)
Edges connect Nodes. 
- A **normal edge** just goes from Node A to Node B.
- A **conditional edge** is an `if/else` statement. 
*Example:* When the `chatbot_node` finishes, a conditional edge checks: "Did the LLM ask to use a tool?" 
- If YES: Route to the `ToolNode` (which runs the tool and loops back to the chatbot).
- If NO: Route to the `END` (return the response to the user).

## 3. The Multi-Agent Flow (How it works in this project)

1. **Input:** User sends symptoms (and optionally a prescription photo).
2. **OCR:** If a photo exists, the `ocr_node` runs.
3. **RAG:** The `retrieval_node` pulls relevant guidelines from ChromaDB.
4. **Reasoning Loop (The Agentic part):**
   - The LLM (`chatbot_node`) looks at everything.
   - It sees the patient needs an ER. It decides to call the `hospital_locator` tool.
   - The graph routes to `ToolNode`, which runs `hospital_locator(location="Mumbai")`.
   - `ToolNode` routes *back* to the `chatbot_node` with the results.
   - The LLM sees the results and generates a final, helpful message.
5. **Output:** The final message is sent to the user.

This complex loop is what makes it a true Agent, not just a chatbot!

## 4. Architecture Diagram

```mermaid
graph TD
    classDef startend fill:#f9f,stroke:#333,stroke-width:2px;
    classDef datanode fill:#bbf,stroke:#333,stroke-width:2px;
    classDef agentnode fill:#fbf,stroke:#333,stroke-width:4px,color:red;
    classDef toolnode fill:#bfb,stroke:#333,stroke-width:2px;

    %% Entry
    Input[/User: Symptoms + Vitals + Photo/] --> START(((START)))
    START:::startend --> N1
    
    %% Sequential Data Prep Pipeline
    subgraph Data Preparation
        N1[prepare_vitals_node<br>Runs Sklearn Model]:::datanode --> N2
        N2[ocr_node<br>Gemini Vision API]:::datanode --> N3
        N3[retrieval_node<br>Queries ChromaDB]:::datanode
    end
    
    N3 --> N4
    
    %% The ReAct Agent Loop
    subgraph The Agentic Loop
        N4{chatbot_node<br>Groq LLM Reasoning}:::agentnode
        
        N4 -- "Requires Tool" --> N5[ToolNode<br>Executes Function]:::toolnode
        N5 -- "Returns Result" --> N4
    end
    
    %% Exit
    N4 -- "Final Answer" --> END(((END))):startend
    END --> Output[/Response sent back to User/]

    %% Tool Definitions
    subgraph Available Tools (backend/agent/tools/)
        T1[[hospital_locator]]
        T2[[pharmacy_locator]]
    end
    
    N5 -.-> T1
    N5 -.-> T2
```
