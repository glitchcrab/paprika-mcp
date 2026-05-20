"""Update recipe tool - modifies recipe fields using find/replace."""

import re
from typing import Any

from mcp.types import TextContent

from ..utils import get_categories, get_remote


async def update_recipe_tool(args: dict[str, Any]) -> list[TextContent]:
    """Update recipe fields using find/replace - DANGEROUS operation."""
    recipe_id = args["id"]
    field = args["field"]
    find = args["find"]
    replace = args["replace"]
    use_regex = args.get("regex", False)

    # Get the remote
    remote = get_remote()

    # Fetch the recipe
    recipe = None
    for r in remote.recipes:
        if r.uid == recipe_id:
            recipe = r
            break

    if not recipe:
        return [
            TextContent(
                type="text",
                text=f"Error: No recipe found with ID '{recipe_id}'",
            )
        ]

    # Get the current field value
    field_value = getattr(recipe, field, None)

    if field_value is None:
        return [
            TextContent(
                type="text",
                text=f"Error: Recipe '{recipe.name}' does not have field '{field}'",
            )
        ]

    # Special handling for categories field (stored internally as a UUID list)
    if field == "categories":
        categories_info = get_categories(remote.bearer_token)
        uid_to_name = categories_info["uid_to_name"]
        name_to_uid = categories_info["name_to_uid"]

        # Convert UUID list to newline-separated names for find/replace
        current_uids = field_value if isinstance(field_value, list) else []
        current_names = "\n".join(
            uid_to_name.get(uid, f"Unknown-{uid[:8]}") for uid in current_uids
        )

        if use_regex:
            try:
                new_names = re.sub(find, replace, current_names)
            except re.error as e:
                return [
                    TextContent(
                        type="text",
                        text=f"Error: Invalid regex pattern '{find}': {str(e)}",
                    )
                ]
        else:
            new_names = current_names.replace(find, replace)

        # Collapse any double-newlines left after removal
        new_names = re.sub(r"\n{2,}", "\n", new_names).strip()

        if new_names == current_names.strip():
            return [
                TextContent(
                    type="text",
                    text=f"No changes made - pattern '{find}' not found in categories of recipe '{recipe.name}'",
                )
            ]

        # Convert names back to UUIDs
        new_uid_list = []
        for name in new_names.split("\n"):
            name = name.strip()
            if not name:
                continue
            uid = name_to_uid.get(name.lower())
            if uid:
                new_uid_list.append(uid)
            else:
                return [
                    TextContent(
                        type="text",
                        text=f"Error: Category '{name}' not found in Paprika — cannot convert back to UUID. No changes were saved.",
                    )
                ]

        recipe.categories = new_uid_list
        try:
            remote.upload_recipe(recipe)
            return [
                TextContent(
                    type="text",
                    text=f"Successfully updated categories in recipe '{recipe.name}' (ID: {recipe_id})\n\nOld categories:\n{current_names}\n\nNew categories:\n{new_names}",
                )
            ]
        except Exception as e:
            return [
                TextContent(
                    type="text",
                    text=f"Error updating recipe '{recipe.name}': {str(e)}",
                )
            ]

    # Perform the find/replace on string fields
    if use_regex:
        try:
            new_value = re.sub(find, replace, field_value)
        except re.error as e:
            return [
                TextContent(
                    type="text", text=f"Error: Invalid regex pattern '{find}': {str(e)}"
                )
            ]
    else:
        new_value = field_value.replace(find, replace)

    # Check if anything changed
    if new_value == field_value:
        return [
            TextContent(
                type="text",
                text=f"No changes made - pattern '{find}' not found in field '{field}' of recipe '{recipe.name}'",
            )
        ]

    # Update the field
    setattr(recipe, field, new_value)

    # Save the recipe
    try:
        remote.upload_recipe(recipe)
        return [
            TextContent(
                type="text",
                text=f"Successfully updated field '{field}' in recipe '{recipe.name}' (ID: {recipe_id})\n\nOld value:\n{field_value}\n\nNew value:\n{new_value}",
            )
        ]
    except Exception as e:
        return [
            TextContent(
                type="text", text=f"Error updating recipe '{recipe.name}': {str(e)}"
            )
        ]


# Tool definition
TOOL_DEFINITION = {
    "name": "update_recipe",
    "description": (
        "Update recipe fields using find/replace. "
        "This is a DANGEROUS operation that requires user confirmation. "
        "Can update any text field in a recipe."
    ),
    "inputSchema": {
        "type": "object",
        "properties": {
            "id": {"type": "string", "description": "Recipe UID to update"},
            "field": {
                "type": "string",
                "enum": [
                    "name",
                    "ingredients",
                    "directions",
                    "notes",
                    "description",
                    "categories",
                    "source",
                    "source_url",
                    "prep_time",
                    "cook_time",
                    "total_time",
                    "servings",
                    "difficulty",
                    "rating",
                    "nutritional_info",
                ],
                "description": "Field to update",
            },
            "find": {"type": "string", "description": "Text to find in the field"},
            "replace": {"type": "string", "description": "Text to replace it with"},
            "regex": {
                "type": "boolean",
                "description": "Whether to treat 'find' as a regex pattern (default: false)",
                "default": False,
            },
        },
        "required": ["id", "field", "find", "replace"],
    },
}
