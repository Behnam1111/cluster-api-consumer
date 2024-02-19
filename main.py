import asyncio
import logging
import argparse
from client import ClusterAPIConsumer

def setup_logging():
    logging.basicConfig(level=logging.INFO)
    return logging.getLogger(__name__)

def parse_args():
    parser = argparse.ArgumentParser(description="Cluster API Consumer")
    parser.add_argument(
        "--action",
        choices=["create", "delete"],
        help="Action to perform: create or delete (default: 'create')."
    )
    parser.add_argument(
        "--group_id",
        type=str,
        help="Group ID (default from environment variable or 'default-group-id')."
    )
    return parser.parse_args()

async def perform_action(consumer, action, group_id):
    action_map = {"create": consumer.create_group, "delete": consumer.delete_group}
    action_func = action_map.get(action)
    if not action_func:
        raise ValueError(f"Invalid action: {action}")

    result = await action_func(group_id)
    return result

async def main_async(args, logger):
    consumer = ClusterAPIConsumer()
    result = await perform_action(consumer, args.action, args.group_id)
    if result:
        logger.info(f"Group '{args.group_id}' {args.action}d successfully.")
    else:
        logger.error(f"Failed to {args.action} group '{args.group_id}'.")

def main():
    logger = setup_logging()
    args = parse_args()

    asyncio.run(main_async(args, logger))

if __name__ == "__main__":
    main()