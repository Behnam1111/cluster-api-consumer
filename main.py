import asyncio
import argparse
from client import ClusterAPIConsumer

import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def main():
    parser = argparse.ArgumentParser(description="Cluster API Consumer")
    parser.add_argument(
        "action",
        choices=["create", "delete"],
        help="Action to perform: create or delete",
    )
    parser.add_argument("group_id", type=str, help="Group ID")
    args = parser.parse_args()

    consumer = ClusterAPIConsumer()

    action_map = {"create": consumer.create_group, "delete": consumer.delete_group}

    action_func = action_map.get(args.action)
    if action_func:
        result = asyncio.run(action_func(args.group_id))
        if result:
            logger.info(f"Group '{args.group_id}' {args.action}d successfully.")
        else:
            logger.error(f"Failed to {args.action} group '{args.group_id}'.")


if __name__ == "__main__":
    main()