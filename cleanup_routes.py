import os
import argparse

def cleanup_routes(delete=False):
    routes_dir = "/home/matt-woodworth/dev/myroofgenius-backend/routes"
    
    keep_list = [
        "__pycache__",
        "ai_agents.py",
        "ai_brain.py",
        "ai_core.py",
        "ai_estimation.py",
        "ai_intelligence.py",
        "complete_erp.py",
        "crm.py",
        "customers.py",
        "elena_roofing_agent.py",
        "erp_core_runtime.py",
        "estimates.py",
        "invoices.py",
        "jobs.py",
        "langgraph_execution.py",
        "lead_capture_ml.py",
        "lead_management.py",
        "memory.py",
        "neural_network.py",
        "relationship_aware.py",
        "route_loader.py",
        "stripe_automation.py",
        "supabase_monitoring.py",
        "tenants.py",
        "voice_commands.py",
        "weathercraft_integration.py",
        "workflows_langgraph.py",
        "workflows.py",
    ]

    delete_list = []
    for filename in os.listdir(routes_dir):
        if filename not in keep_list:
            delete_list.append(os.path.join(routes_dir, filename))

    if not delete:
        print("The following files have been identified as boilerplate and are proposed for deletion:")
        for filepath in sorted(delete_list):
            print(filepath)
        print("\nTo delete these files, run the script with the --delete flag.")
    else:
        print("Deleting the following files:")
        for filepath in sorted(delete_list):
            print(f"Deleting: {filepath}")
            try:
                os.remove(filepath)
            except OSError as e:
                print(f"Error deleting file {filepath}: {e}")
        print("\nCleanup complete.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Clean up boilerplate route files.")
    parser.add_argument("--delete", action="store_true", help="Actually delete the files.")
    args = parser.parse_args()
    cleanup_routes(args.delete)
