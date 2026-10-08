from pathlib import Path
from urllib import response
from playwright.sync_api import sync_playwright
from config import GRAYLOG_URL, GRAYLOG_USERNAME, GRAYLOG_PASSWORD


# =========================================================
# SETTINGS
# =========================================================

TPA_NAME = ""
OUTPUT_DIR = Path.home() / "Desktop" / "graylog_outputs"
TPA_GRAYLOG_NAMES = {
    "BPP": "Benefit Plans Plus LLC",
}


def get_graylog_tpa_name(tpa_name):
    """Return the TPA name exactly as displayed/used by Graylog."""
    return TPA_GRAYLOG_NAMES.get(
        str(tpa_name).strip(),
        str(tpa_name).strip()
    )


# =========================================================
# HELPER
# =========================================================

def visible(locator):
    for i in range(locator.count()):
        try:
            item = locator.nth(i)
            if item.is_visible():
                return item
        except:
            pass
    return None


# =========================================================
# COPY ONLY LOGIN QUERY
# =========================================================

def copy_login_query(page):

    print()
    print("========================================")
    print("COPY ONLY LOGIN QUERY")
    print("========================================")

    graylog_tpa_name = get_graylog_tpa_name(TPA_NAME)

    body = page.locator("body").inner_text()

    start = body.find("gl2_source_input:")
    if start == -1:
        raise Exception("gl2_source_input not found.")

    user_logged_in = body.find('"User logged in"', start)
    if user_logged_in == -1:
        raise Exception('"User logged in" was not found in the query.')

    groups_pos = body.find("GROUPS:", user_logged_in)
    if groups_pos == -1:
        raise Exception("GROUPS filter not found in the User logged in query.")

    # The UI value can differ from the value used by Graylog.
    # Example: UI = BPP, Graylog = Benefit Plans Plus LLC.
    tpa_pos = body.find(graylog_tpa_name, groups_pos)
    if tpa_pos == -1:
        raise Exception(
            f'Correct Graylog TPA "{graylog_tpa_name}" not found in the GROUPS filter.'
        )

    end = tpa_pos + len(graylog_tpa_name)

    # Include the closing quote after the selected TPA when Graylog shows
    # the GROUPS value in quotes, e.g. GROUPS:"/Benefit Plans Plus LLC".
    if end < len(body) and body[end] == '"':
        end += 1

    query = body[start:end]

    # Graylog may render escaped slashes/quotes in this editor.
    # Remove only those display escapes; the query is still copied from the UI.
    query = query.replace('\\"', '"')
    query = query.replace('\\"', '"')
    query = query.replace('\\\\', '\\')
    query = " ".join(query.split())
    query = query.replace('\\\\', '\\')
    query = " ".join(query.split())

    print()
    print("QUERY COPIED:")
    print(query)

    if (
        "gl2_source_input:" not in query
        or
        '"User logged in"' not in query
        or
        "GROUPS:" not in query
        or
        graylog_tpa_name not in query
    ):
        raise Exception(
            "This is not the User logged in query for the selected TPA."
        )

    print()
    print("QUERY VERIFIED SUCCESSFULLY.")

    return query


# =========================================================
# FIND MESSAGES WIDGET FOR SELECTED TPA
# =========================================================

def find_messages_widget_title_for_tpa(page, tpa_name):

    print()
    print("========================================")
    print("FINDING MESSAGES WIDGET FOR TPA")
    print("========================================")

    graylog_tpa_name = get_graylog_tpa_name(tpa_name)

    print(
        f'Looking for Messages widget containing TPA: {graylog_tpa_name}'
    )

    # Graylog can render the title with different escaping/formatting,
    # for example:
    #   Messages for GROUPS:"/Benefit Plans Plus LLC"
    #   Messages for GROUPS:"/InWest Retirement Solutions"
    # Therefore, do not rely on one exact title string.
    locators = [
        page.locator('text=/^Messages for GROUPS:/i'),
        page.get_by_text(
            f'Messages for GROUPS:"/{graylog_tpa_name}"',
            exact=True
        ),
        page.get_by_text(
            f'Messages for GROUPS:"{graylog_tpa_name}"',
            exact=True
        ),
    ]

    candidates = []
    seen = set()

    for locator in locators:
        for i in range(locator.count()):
            try:
                item = locator.nth(i)

                if not item.is_visible():
                    continue

                text = item.inner_text().strip()

                # Must be a Messages widget title and must contain the
                # actual Graylog TPA name. Backslash/quote differences are fine.
                if not text.lower().startswith("messages for groups:"):
                    continue

                if graylog_tpa_name.lower() not in text.lower():
                    continue

                box = item.bounding_box()

                if not box:
                    continue

                key = (
                    round(box["x"], 1),
                    round(box["y"], 1),
                    text
                )

                if key in seen:
                    continue

                seen.add(key)
                candidates.append((item, box, text))

            except Exception:
                pass

    if not candidates:
        page.screenshot(
            path="messages_widget_error.png",
            full_page=True
        )

        raise Exception(
            f'Messages widget for TPA "{graylog_tpa_name}" could not be found.'
        )

    # The newly opened Messages widget is normally the lowest visible one.
    message_title, title_box, title_text = max(
        candidates,
        key=lambda x: x[1]["y"]
    )

    print(
        f'Messages widget found: text={title_text!r}, '
        f'x={title_box["x"]:.0f}, y={title_box["y"]:.0f}'
    )

    return message_title


# =========================================================
# FIND LOGIN MESSAGE EDIT
# =========================================================

def find_login_message_edit(
    page,
    message_title
):

    print()
    print("========================================")
    print("FINDING MESSAGE WIDGET EDIT")
    print("========================================")

    title_box = message_title.bounding_box()

    if not title_box:
        raise Exception(
            "Message title position unavailable."
        )

    # Move cursor over Messages widget.
    message_title.hover()

    page.wait_for_timeout(
        1500
    )

    edits = page.locator(
        'button[title="Edit"], '
        'button[aria-label="Edit"], '
        '[data-original-title="Edit"]'
    )

    best = None
    best_distance = 999999

    for i in range(edits.count()):

        try:

            edit = edits.nth(i)

            if not edit.is_visible():
                continue

            box = edit.bounding_box()

            if not box:
                continue

            print(
                f"Edit {i}: "
                f"x={box['x']:.0f}, "
                f"y={box['y']:.0f}"
            )

            distance = abs(
                box["y"] -
                title_box["y"]
            )

            if distance < 80:

                if distance < best_distance:

                    best = edit
                    best_distance = distance

        except:
            pass

    if best is None:

        raise Exception(
            "Correct Messages Edit button not found."
        )

    print(
        "FOUND CORRECT MESSAGE WIDGET EDIT"
    )

    return best


# =========================================================
# OPEN SEARCH
# =========================================================

def open_search(page):

    print()
    print("========================================")
    print("OPENING GRAYLOG SEARCH")
    print("========================================")

    base_url = GRAYLOG_URL.split(
        "/dashboards/"
    )[0]

    search_url = (
        base_url +
        "/search"
    )

    page.goto(
        search_url,
        wait_until="domcontentloaded",
        timeout=60000
    )

    page.wait_for_timeout(
        3000
    )

    print(
        "Search page opened."
    )

    print(
        "Current URL:",
        page.url
    )


# =========================================================
# PASTE QUERY
# =========================================================

def paste_query(
    page,
    query
):

    print()
    print("========================================")
    print("PASTING LOGIN QUERY")
    print("========================================")

    print()
    print("ONLY QUERY:")
    print(query)

    # Search bar shown in your screenshot.
    page.mouse.click(
        500,
        150
    )

    page.wait_for_timeout(
        300
    )

    page.keyboard.press(
        "Control+A"
    )

    page.keyboard.press(
        "Backspace"
    )

    page.keyboard.insert_text(
        query
    )

    page.wait_for_timeout(
        800
    )

    print(
        "QUERY PASTED."
    )


# =========================================================
# EXECUTE SEARCH
# =========================================================

def execute_search(page):

    print()
    print("========================================")
    print("EXECUTING SEARCH")
    print("========================================")

    search_button = page.locator(
        'button[title*="Perform search"]'
    )

    button = visible(
        search_button
    )

    if button:

        button.click()

    else:

        # Graylog search button position.
        page.mouse.click(
            105,
            150
        )

    page.wait_for_timeout(
        3000
    )

    print(
        "SEARCH EXECUTED."
    )


# =========================================================
# CLICK BLACK TRIANGLE
# =========================================================

def click_black_triangle(page):

    print()
    print("========================================")
    print("CLICKING BLACK TRIANGLE")
    print("========================================")

    triangle = page.locator(
        'button[aria-label="Open time range preset select"]'
    )

    button = visible(
        triangle
    )

    if button is None:

        raise Exception(
            "Black triangle not found."
        )

    box = button.bounding_box()

    if box:

        print(
            f"Triangle position: "
            f"x={box['x']:.0f}, "
            f"y={box['y']:.0f}, "
            f"w={box['width']:.0f}, "
            f"h={box['height']:.0f}"
        )

    button.click()

    page.wait_for_timeout(
        800
    )

    print(
        "BLACK TRIANGLE CLICKED."
    )


# =========================================================
# SELECT ALL MESSAGES
# =========================================================

def select_all_messages(page):

    print()
    print("========================================")
    print("SELECTING ALL MESSAGES")
    print("========================================")

    # Exact text first.
    options = page.get_by_text(
        "All messages",
        exact=True
    )

    for i in range(options.count()):

        try:

            option = options.nth(i)

            if not option.is_visible():
                continue

            print(
                "FOUND: All messages"
            )

            option.click(
                force=True
            )

            page.wait_for_timeout(
                2500
            )

            print(
                "ALL MESSAGES SELECTED."
            )

            return

        except:
            pass

    # Case-insensitive fallback.
    options = page.locator(
        "text=/^All messages$/i"
    )

    for i in range(options.count()):

        try:

            option = options.nth(i)

            if not option.is_visible():
                continue

            print(
                "FOUND: All messages"
            )

            option.click(
                force=True
            )

            page.wait_for_timeout(
                2500
            )

            print(
                "ALL MESSAGES SELECTED."
            )

            return

        except:
            pass

    page.screenshot(
        path="all_messages_error.png",
        full_page=True
    )

    raise Exception(
        "All messages option not found."
    )


# =========================================================
# FIND ALL MESSAGES WIDGET
# =========================================================

def find_all_messages_widget(page):

    titles = page.locator(
        "text=/^All Messages$/i"
    )

    found = []

    for i in range(
        titles.count()
    ):

        try:

            title = titles.nth(i)

            if not title.is_visible():
                continue

            box = title.bounding_box()

            if box:
                found.append(
                    (title, box)
                )

        except:
            pass

    if not found:

        raise Exception(
            "All Messages widget not found."
        )

    # Choose the visible All Messages widget.
    title, title_box = max(
        found,
        key=lambda x: x[1]["y"]
    )

    ancestors = title.locator(
        "xpath=ancestor::*"
    )

    widget = None
    smallest_area = None

    for i in range(
        ancestors.count()
    ):

        try:

            candidate = ancestors.nth(i)

            if not candidate.is_visible():
                continue

            box = candidate.bounding_box()

            if not box:
                continue

            if box["width"] < 700:
                continue

            if box["height"] < 150:
                continue

            area = (
                box["width"] *
                box["height"]
            )

            if (
                smallest_area is None
                or
                area < smallest_area
            ):

                widget = candidate
                smallest_area = area

        except:
            pass

    if widget is None:

        raise Exception(
            "All Messages widget container not found."
        )

    return (
        widget,
        title,
        title_box
    )


# =========================================================
# HOVER ALL MESSAGES + TOP RIGHT EDIT
# =========================================================

def edit_all_messages(page):

    print()
    print("========================================")
    print("EDIT ALL MESSAGES WIDGET")
    print("========================================")

    (
        widget,
        title,
        title_box
    ) = find_all_messages_widget(
        page
    )

    widget_box = widget.bounding_box()

    if not widget_box:

        raise Exception(
            "Widget position unavailable."
        )

    print(
        "FOUND: All Messages widget"
    )

    # IMPORTANT:
    # Move mouse over widget first.
    # Graylog only shows Edit on hover.
    page.mouse.move(
        widget_box["x"] +
        widget_box["width"] / 2,

        widget_box["y"] + 35
    )

    page.wait_for_timeout(
        1800
    )

    print(
        "Cursor moved over All Messages."
    )

    edits = widget.locator(
        'button[title="Edit"], '
        'button[aria-label="Edit"], '
        '[data-original-title="Edit"]'
    )

    candidates = []

    for i in range(edits.count()):

        try:

            edit = edits.nth(i)

            if not edit.is_visible():
                continue

            box = edit.bounding_box()

            if not box:
                continue

            print(
                f"Edit {i}: "
                f"x={box['x']:.0f}, "
                f"y={box['y']:.0f}"
            )

            # Only header icons.
            if (
                widget_box["y"] - 20
                <= box["y"]
                <= widget_box["y"] + 100
            ):

                candidates.append(
                    (edit, box)
                )

        except:
            pass

    if not candidates:

        page.screenshot(
            path="all_messages_edit_error.png",
            full_page=True
        )

        raise Exception(
            "Top-right Edit not found."
        )

    # IMPORTANT:
    # Select the RIGHT-MOST Edit icon.
    edit_button, edit_box = max(
        candidates,
        key=lambda x: x[1]["x"]
    )

    print(
        "FOUND TOP-RIGHT EDIT"
    )

    print(
        "Clicking top-right Edit..."
    )

    edit_button.click(
        force=True
    )

    page.wait_for_timeout(
        2500
    )

    print(
        "ALL MESSAGES EDITOR OPENED."
    )


# =========================================================
# CLICK ADD A FIELD
# =========================================================

def click_add_field(page):

    print()
    print("========================================")
    print("CLICKING ADD A FIELD")
    print("========================================")

    # Graylog uses React-Select.
    #
    # The visible text "Add a field" is a placeholder.
    # We click the React-Select control instead.

    placeholders = page.locator(
        'div[id$="-placeholder"]'
    ).filter(
        has_text="Add a field"
    )

    print(
        "Add a field elements found:",
        placeholders.count()
    )

    selected = None

    for i in range(
        placeholders.count()
    ):

        try:

            item = placeholders.nth(i)

            if not item.is_visible():
                continue

            box = item.bounding_box()

            if not box:
                continue

            print(
                f"Add a field {i}: "
                f"x={box['x']:.0f}, "
                f"y={box['y']:.0f}, "
                f"w={box['width']:.0f}, "
                f"h={box['height']:.0f}"
            )

            # Left side Fields section.
            if (
                box["x"] < 600
                and
                box["y"] > 200
                and
                box["width"] > 150
            ):

                selected = item
                break

        except:
            pass

    if selected is None:

        page.screenshot(
            path="add_field_error.png",
            full_page=True
        )

        raise Exception(
            "Correct Add a field not found."
        )

    print()
    print(
        "CORRECT ADD A FIELD FOUND."
    )

    # -----------------------------------------------------
    # Go from placeholder to React-Select control.
    # -----------------------------------------------------

    parent = selected.locator(
        "xpath=.."
    )

    control = parent.locator(
        "xpath=.."
    )

    control_box = control.bounding_box()

    if not control_box:

        control = parent
        control_box = parent.bounding_box()

    if not control_box:

        raise Exception(
            "React-Select control not found."
        )

    print(
        f"Control: "
        f"x={control_box['x']:.0f}, "
        f"y={control_box['y']:.0f}, "
        f"w={control_box['width']:.0f}, "
        f"h={control_box['height']:.0f}"
    )

    # Move mouse over Add a field.
    page.mouse.move(
        control_box["x"] +
        control_box["width"] / 2,

        control_box["y"] +
        control_box["height"] / 2
    )

    page.wait_for_timeout(
        500
    )

    print(
        "Clicking Add a field..."
    )

    control.click(
        force=True
    )

    page.wait_for_timeout(
        1000
    )

    print()
    print(
        "ADD A FIELD DROPDOWN OPENED."
    )


# =========================================================
# TYPE USERNAME
# =========================================================

def type_username(page):

    print()
    print("========================================")
    print('TYPE "username"')
    print("========================================")

    page.wait_for_timeout(
        500
    )

    inputs = page.locator(
        "input"
    )

    selected_input = None

    for i in range(
        inputs.count()
    ):

        try:

            inp = inputs.nth(i)

            if not inp.is_visible():
                continue

            if not inp.is_editable():
                continue

            box = inp.bounding_box()

            if not box:
                continue

            print(
                f"Input {i}: "
                f"x={box['x']:.0f}, "
                f"y={box['y']:.0f}, "
                f"w={box['width']:.0f}"
            )

            # Field selector is left side.
            if (
                box["x"] < 600
                and
                box["y"] > 250
            ):

                selected_input = inp
                break

        except:
            pass

    if selected_input is None:

        page.screenshot(
            path="username_input_error.png",
            full_page=True
        )

        raise Exception(
            "Username field selector input not found."
        )

    print(
        "FIELD SELECTOR INPUT FOUND."
    )

    selected_input.click()

    selected_input.fill(
        "username"
    )

    page.wait_for_timeout(
        1200
    )

    print()
    print(
        'TYPED: username'
    )


# =========================================================
# SELECT LOWERCASE username
# =========================================================

def select_username(page):

    print()
    print("========================================")
    print('SELECTING LOWERCASE "username"')
    print("========================================")

    page.wait_for_timeout(800)

    # Graylog shows the dropdown option as:
    #
    # text_fields
    # username
    #
    # Click the complete dropdown row.

    options = page.locator('[role="option"]')

    print(
        "React option count:",
        options.count()
    )

    for i in range(options.count()):

        try:

            option = options.nth(i)

            if not option.is_visible():
                continue

            text = option.inner_text().strip()

            print(
                f"React option {i}: {repr(text)}"
            )

            lines = [
                line.strip().lower()
                for line in text.splitlines()
                if line.strip()
            ]

            # Exact dropdown row wanted:
            # text_fields / username
            if (
                "username" in lines
                and
                "text_fields" in lines
            ):

                box = option.bounding_box()

                if box:
                    print(
                        f"FOUND USERNAME OPTION: "
                        f"x={box['x']:.0f}, "
                        f"y={box['y']:.0f}, "
                        f"w={box['width']:.0f}, "
                        f"h={box['height']:.0f}"
                    )

                print()
                print(
                    "FOUND DROPDOWN: text_fields / username"
                )

                print(
                    "CLICKING THE DROPDOWN USERNAME..."
                )

                option.click(force=True)

                page.wait_for_timeout(1500)

                print()
                print(
                    "USERNAME SELECTED SUCCESSFULLY."
                )

                return

        except Exception as e:

            print(
                f"Option {i} skipped: {e}"
            )

    # =====================================================
    # FALLBACK
    # =====================================================

    print()
    print(
        "Trying dropdown row fallback..."
    )

    result = page.evaluate("""
        () => {

            const options =
                [...document.querySelectorAll('[role="option"]')];

            for (const el of options) {

                if (!el.offsetParent)
                    continue;

                const lines =
                    (el.innerText || '')
                        .split(/\\r?\
/)
                        .map(x => x.trim().toLowerCase())
                        .filter(Boolean);

                if (
                    lines.includes('text_fields') &&
                    lines.includes('username')
                ) {

                    el.click();

                    return true;
                }
            }

            return false;
        }
    """)

    if result:

        page.wait_for_timeout(1500)

        print()
        print(
            "USERNAME SELECTED SUCCESSFULLY."
        )

        return

    page.screenshot(
        path="username_selection_error.png",
        full_page=True
    )

    raise Exception(
        'Could not click the "text_fields / username" dropdown option.'
    )


def verify_username_added(page):

    print()
    print("========================================")
    print("VERIFYING USERNAME FIELD")
    print("========================================")

    # Wait for React UI update.
    page.wait_for_timeout(
        1000
    )

    body = page.locator(
        "body"
    ).inner_text()

    # Look for username in Fields section.
    if "username" in body:

        print(
            'FOUND "username" IN PAGE.'
        )

        print()
        print(
            "USERNAME FIELD ADDED SUCCESSFULLY."
        )

        return True

    print(
        'WARNING: "username" not found after click.'
    )

    return False



# =========================================================
# TYPE GROUPS
# =========================================================
def type_groups(page):

    print()
    print("========================================")
    print('TYPE "GROUPS"')
    print("========================================")

    page.wait_for_timeout(500)

    inputs = page.locator(
        "input"
    )

    selected_input = None

    for i in range(inputs.count()):

        try:

            inp = inputs.nth(i)

            if not inp.is_visible():
                continue

            if not inp.is_editable():
                continue

            box = inp.bounding_box()

            if not box:
                continue

            print(
                f"Input {i}: "
                f"x={box['x']:.0f}, "
                f"y={box['y']:.0f}, "
                f"w={box['width']:.0f}"
            )

            # Field selector is on the left side.
            if (
                box["x"] < 600
                and
                box["y"] > 250
            ):

                selected_input = inp
                break

        except:
            pass

    if selected_input is None:

        page.screenshot(
            path="groups_input_error.png",
            full_page=True
        )

        raise Exception(
            'GROUPS field selector input not found.'
        )

    print(
        "FIELD SELECTOR INPUT FOUND."
    )

    selected_input.click()

    selected_input.fill(
        "GROUPS"
    )

    page.wait_for_timeout(
        1200
    )

    print()
    print(
        'TYPED: GROUPS'
    )


# =========================================================
# SELECT GROUPS
# =========================================================
def select_groups(page):

    print()
    print("========================================")
    print('SELECTING "GROUPS"')
    print("========================================")

    page.wait_for_timeout(
        800
    )

    options = page.locator(
        '[role="option"]'
    )

    print(
        "React option count:",
        options.count()
    )

    for i in range(options.count()):

        try:

            option = options.nth(i)

            if not option.is_visible():
                continue

            text = option.inner_text().strip()

            print(
                f"React option {i}: {repr(text)}"
            )

            lines = [
                line.strip().lower()
                for line in text.splitlines()
                if line.strip()
            ]

            if (
                "groups" in lines
                and
                "text_fields" in lines
            ):

                box = option.bounding_box()

                if box:
                    print(
                        f"FOUND GROUPS OPTION: "
                        f"x={box['x']:.0f}, "
                        f"y={box['y']:.0f}, "
                        f"w={box['width']:.0f}, "
                        f"h={box['height']:.0f}"
                    )

                print()
                print(
                    "FOUND DROPDOWN: text_fields / GROUPS"
                )

                print(
                    "CLICKING THE DROPDOWN GROUPS..."
                )

                option.click(
                    force=True
                )

                page.wait_for_timeout(
                    1500
                )

                print()
                print(
                    "GROUPS SELECTED SUCCESSFULLY."
                )

                return

        except Exception as e:

            print(
                f"Option {i} skipped: {e}"
            )

    # =====================================================
    # FALLBACK
    # =====================================================

    print()
    print(
        "Trying GROUPS dropdown row fallback..."
    )

    result = page.evaluate("""
        () => {

            const options =
                [...document.querySelectorAll('[role="option"]')];

            for (const el of options) {

                if (!el.offsetParent)
                    continue;

                const lines =
                    (el.innerText || '')
                        .split(/\\r?\
/)
                        .map(x => x.trim().toLowerCase())
                        .filter(Boolean);

                if (
                    lines.includes('text_fields') &&
                    lines.includes('groups')
                ) {

                    el.click();

                    return true;
                }
            }

            return false;
        }
    """)

    if result:

        page.wait_for_timeout(
            1500
        )

        print()
        print(
            "GROUPS SELECTED SUCCESSFULLY."
        )

        return

    page.screenshot(
        path="groups_selection_error.png",
        full_page=True
    )

    raise Exception(
        'Could not click the "text_fields / GROUPS" dropdown option.'
    )


# =========================================================
# VERIFY GROUPS ADDED
# =========================================================
def verify_groups_added(page):

    print()
    print("========================================")
    print("VERIFYING GROUPS FIELD")
    print("========================================")

    page.wait_for_timeout(
        1000
    )

    body = page.locator(
        "body"
    ).inner_text()

    if "GROUPS" in body:

        print(
            'FOUND "GROUPS" IN PAGE.'
        )

        print()
        print(
            "GROUPS FIELD ADDED SUCCESSFULLY."
        )

        return True

    print(
        'WARNING: "GROUPS" not found after click.'
    )

    return False


# =========================================================
# SCROLL TO BOTTOM
# =========================================================

def scroll_to_bottom(page):

    print()
    print("========================================")
    print("SCROLLING TO BOTTOM")
    print("========================================")

    # Move over the main Graylog content area.
    page.mouse.move(800, 700)

    # First use normal mouse-wheel scrolling.
    for _ in range(15):
        page.mouse.wheel(0, 1200)
        page.wait_for_timeout(200)

    # Graylog can use an internal scroll container.
    # Scroll every visible container that actually has
    # more content than its visible height.
    page.evaluate("""
        () => {

            const elements =
                [...document.querySelectorAll('*')];

            for (const el of elements) {

                const style =
                    window.getComputedStyle(el);

                if (
                    (
                        style.overflowY === 'auto' ||
                        style.overflowY === 'scroll'
                    ) &&
                    el.scrollHeight > el.clientHeight
                ) {
                    el.scrollTop = el.scrollHeight;
                }
            }

            window.scrollTo(
                0,
                document.documentElement.scrollHeight
            );

            document.body.scrollTop =
                document.body.scrollHeight;
        }
    """)

    page.wait_for_timeout(1000)

    print("SCROLL COMPLETED.")
    print()




# =========================================================
# SCROLL LEFT EDITOR PANEL TO BOTTOM
# =========================================================

def scroll_left_editor_to_bottom(page):

    print()
    print("========================================")
    print("SCROLLING LEFT EDITOR PANEL TO BOTTOM")
    print("========================================")

    # Move the mouse into the LEFT editor panel.
    page.mouse.move(250, 400)
    page.wait_for_timeout(500)

    print("Scrolling LEFT panel once...")

    # ONE large scroll only.
    page.mouse.wheel(0, 10000)
    page.wait_for_timeout(1500)

    print()
    print("LEFT EDITOR PANEL SCROLLED TO BOTTOM.")


# =========================================================
# CLICK UPDATE WIDGET
# =========================================================

def click_update_widget(page):
    print()
    print("========================================")
    print("CLICKING UPDATE WIDGET")
    print("========================================")

    page.wait_for_timeout(1000)

    # The actual Graylog button text is "Update widget"
    # (lowercase w), as shown in the UI.
    button = page.get_by_role(
        "button",
        name="Update widget",
        exact=True
    )

    for i in range(button.count()):
        try:
            item = button.nth(i)
            if not item.is_visible():
                continue

            box = item.bounding_box()
            if box:
                print(
                    f"FOUND Update widget: "
                    f"x={box['x']:.0f}, "
                    f"y={box['y']:.0f}, "
                    f"w={box['width']:.0f}, "
                    f"h={box['height']:.0f}"
                )

            item.scroll_into_view_if_needed()
            page.wait_for_timeout(300)
            item.click(force=True)
            page.wait_for_timeout(3000)

            print("UPDATE WIDGET CLICKED SUCCESSFULLY.")
            return
        except Exception as e:
            print(f"Button {i} skipped: {e}")

    # Fallback: search all visible buttons case-insensitively.
    all_buttons = page.locator("button")
    for i in range(all_buttons.count()):
        try:
            item = all_buttons.nth(i)
            if not item.is_visible():
                continue

            text = item.inner_text().strip()
            if text.lower() != "update widget":
                continue

            box = item.bounding_box()
            if box:
                print(
                    f"FOUND Update widget by fallback: "
                    f"x={box['x']:.0f}, "
                    f"y={box['y']:.0f}"
                )

            item.scroll_into_view_if_needed()
            page.wait_for_timeout(300)
            item.click(force=True)
            page.wait_for_timeout(3000)

            print("UPDATE WIDGET CLICKED SUCCESSFULLY.")
            return
        except Exception as e:
            print(f"Fallback button {i} skipped: {e}")

    page.screenshot(
        path="update_widget_error.png",
        full_page=True
    )

    raise Exception(
        'Update widget button could not be found after the single left-panel scroll.'
    )


# =========================================================
# HOVER ALL MESSAGES + CLICK DOWNLOAD
# =========================================================
def download_all_messages_csv(page):
    print()
    print("========================================")
    print("MOVE CURSOR AND CLICK FIRST DOWNLOAD ICON")
    print("========================================")

    # ---------------------------------------------------------
    # FIND ALL MESSAGES WIDGET
    # ---------------------------------------------------------
    widget, title, title_box = find_all_messages_widget(page)
    widget_box = widget.bounding_box()

    if not widget_box:
        raise Exception(
            "All Messages widget position unavailable."
        )

    print("FOUND: All Messages widget")

    # ---------------------------------------------------------
    # HOVER WIDGET
    # ---------------------------------------------------------
    hover_x = (
        widget_box["x"] +
        widget_box["width"] / 2
    )
    hover_y = widget_box["y"] + 35

    print(
        f"Moving cursor to All Messages: "
        f"x={hover_x:.0f}, y={hover_y:.0f}"
    )

    page.mouse.move(
        hover_x,
        hover_y
    )

    page.wait_for_timeout(2000)

    print("Cursor moved over All Messages.")

    # ---------------------------------------------------------
    # FIND TOOLBAR ICONS
    #
    # The first/leftmost toolbar icon is:
    # Export all search results
    # ---------------------------------------------------------
    print()
    print("SEARCHING FOR FIRST TOOLBAR ICON...")

    candidates = []

    selectors = [
        "button",
        '[role="button"]',
        '[data-testid]',
    ]

    for selector in selectors:
        locator = widget.locator(selector)

        for i in range(locator.count()):
            try:
                item = locator.nth(i)

                if not item.is_visible():
                    continue

                box = item.bounding_box()

                if not box:
                    continue

                in_header = (
                    box["y"] >= widget_box["y"] - 10
                    and
                    box["y"] <= widget_box["y"] + 75
                )

                in_right_side = (
                    box["x"] >
                    widget_box["x"] +
                    widget_box["width"] -
                    250
                )

                if not (in_header and in_right_side):
                    continue

                if box["width"] > 80 or box["height"] > 80:
                    continue

                duplicate = False

                for _, existing_box in candidates:
                    if (
                        abs(existing_box["x"] - box["x"]) < 3
                        and
                        abs(existing_box["y"] - box["y"]) < 3
                    ):
                        duplicate = True
                        break

                if duplicate:
                    continue

                try:
                    aria = item.get_attribute(
                        "aria-label"
                    ) or ""
                except:
                    aria = ""

                try:
                    title_attr = item.get_attribute(
                        "title"
                    ) or ""
                except:
                    title_attr = ""

                print(
                    f"Toolbar candidate: "
                    f"x={box['x']:.0f}, "
                    f"y={box['y']:.0f}, "
                    f"w={box['width']:.0f}, "
                    f"h={box['height']:.0f}, "
                    f"aria={aria!r}, "
                    f"title={title_attr!r}"
                )

                candidates.append(
                    (item, box, aria, title_attr)
                )

            except Exception:
                pass

    # ---------------------------------------------------------
    # SELECT FIRST DOWNLOAD ICON
    # Prefer the element explicitly identified by Graylog as
    # "Export all search results".
    # ---------------------------------------------------------
    download_button = None
    download_box = None

    for item, box, aria, title_attr in candidates:
        if (
            aria.lower() ==
            "export all search results"
            or
            title_attr.lower() ==
            "export all search results"
        ):
            download_button = item
            download_box = box
            break

    # If accessibility name is unavailable, use leftmost icon.
    if download_button is None and candidates:
        candidates.sort(
            key=lambda x: x[1]["x"]
        )

        download_button = candidates[0][0]
        download_box = candidates[0][1]

    if download_button is None:
        page.screenshot(
            path="download_button_error.png",
            full_page=True
        )

        raise Exception(
            "First Download icon could not be found."
        )

    print()
    print(
        "FIRST DOWNLOAD ICON FOUND: "
        f"x={download_box['x']:.0f}, "
        f"y={download_box['y']:.0f}"
    )

    # ---------------------------------------------------------
    # HOVER AND CLICK THE FIRST DOWNLOAD ICON
    # ---------------------------------------------------------
    download_button.hover()

    page.wait_for_timeout(800)

    print(
        "CLICKING FIRST DOWNLOAD ICON..."
    )

    download_button.click(
        force=True
    )

    page.wait_for_timeout(1500)

    print()
    print(
        "DOWNLOAD ICON CLICKED."
    )
    print(
        "Waiting for Export all search results popup..."
    )

    # ---------------------------------------------------------
    # WAIT FOR POPUP
    # ---------------------------------------------------------
    popup_title = page.get_by_text(
        "Export all search results",
        exact=True
    )

    popup_title.wait_for(
        state="visible",
        timeout=10000
    )

    print(
        "EXPORT ALL SEARCH RESULTS POPUP OPENED."
    )

    # ---------------------------------------------------------
    # FIND BLUE START DOWNLOAD BUTTON
    # ---------------------------------------------------------
    print()
    print(
        "FINDING BLUE START DOWNLOAD BUTTON..."
    )

    start_download = page.get_by_role(
        "button",
        name="Start Download",
        exact=True
    )

    selected_button = None

    for i in range(start_download.count()):
        try:
            button = start_download.nth(i)

            if not button.is_visible():
                continue

            box = button.bounding_box()

            if box:
                print(
                    f"Start Download {i}: "
                    f"x={box['x']:.0f}, "
                    f"y={box['y']:.0f}, "
                    f"w={box['width']:.0f}, "
                    f"h={box['height']:.0f}"
                )

            selected_button = button
            break

        except Exception as e:
            print(
                f"Start Download {i} skipped: {e}"
            )

    # ---------------------------------------------------------
    # FALLBACK
    # ---------------------------------------------------------
    if selected_button is None:
        buttons = page.locator("button")

        for i in range(buttons.count()):
            try:
                button = buttons.nth(i)

                if not button.is_visible():
                    continue

                if (
                    button.inner_text()
                    .strip()
                    .lower()
                    != "start download"
                ):
                    continue

                selected_button = button
                break

            except Exception:
                pass

    if selected_button is None:
        page.screenshot(
            path="start_download_error.png",
            full_page=True
        )

        raise Exception(
            "Blue Start Download button not found."
        )

    # ---------------------------------------------------------
    # CLICK START DOWNLOAD
    #
    # IMPORTANT:
    # DO NOT rename the file.
    #
    # Playwright receives the filename supplied by Graylog.
    # We only print suggested_filename and let Playwright save
    # the download using its original suggested filename.
    # ---------------------------------------------------------
    print()
    print(
    "FOUND BLUE START DOWNLOAD BUTTON."
)
    print(
    "CLICKING START DOWNLOAD..."
)

    print()
    print("CLICKING START DOWNLOAD...")

    responses = []

    def capture_response(response):
        try:
            url = response.url

            if (
                "export" in url.lower()
            or "csv" in url.lower()
            or "search" in url.lower()
            or "messages" in url.lower()
        ):
                responses.append(response)

                print()
                print("DOWNLOAD-RELATED RESPONSE:")
                print("STATUS:", response.status)
                print("URL:", url)

        except Exception:
            pass


    page.on(
    "response",
        capture_response
)

    with page.expect_download(
        timeout=120000
) as download_info:

        selected_button.click(
            force=True
    )

    download = download_info.value

    print()
    print("DOWNLOAD EVENT RECEIVED.")

    original_filename = download.suggested_filename

    print()
    print("GRAYLOG ORIGINAL FILENAME:")
    print(original_filename)

    print()
    print("WAITING FOR DOWNLOAD TO COMPLETE...")

    failure = download.failure()

    print()
    print("DOWNLOAD FAILURE:")
    print(failure)

    if failure:
        print()
        print("CAPTURED RESPONSES:")

        for response in responses:
            try:
                print(
                    response.status,
                    response.url
            )
            except Exception:
                pass

        raise Exception(
            f"Graylog export download failed: {failure}"
    )

    download = download_info.value

    print()
    print(
    "DOWNLOAD EVENT RECEIVED."
)

# ---------------------------------------------------------
# ORIGINAL GRAYLOG FILENAME
# ---------------------------------------------------------
    original_filename = (
    download.suggested_filename
)

    print()
    print(
    "GRAYLOG ORIGINAL FILENAME:"
)
    print(
    original_filename
)

# ---------------------------------------------------------
# CHECK DOWNLOAD STATUS
# ---------------------------------------------------------
    

# ---------------------------------------------------------
# SAVE USING GRAYLOG'S ORIGINAL FILENAME
#
# IMPORTANT:
# NEVER use a custom filename.
# ---------------------------------------------------------
    OUTPUT_DIR.mkdir(
    parents=True,
    exist_ok=True
)

    output_file = (
    OUTPUT_DIR /
    original_filename
)

    print()
    print(
        "SAVING TO:"
    )
    print(
        output_file.resolve()

)

    download.save_as(
    str(output_file)
)

    print()
    print(
        "SECOND CSV DOWNLOAD COMPLETED."
    )

    print(
        "GRAYLOG ORIGINAL FILENAME:"
    )

    print(
    original_filename
)

    print()
    print(
        "SAVED TO:"
    )
    print(
        output_file.resolve()

)

    print()
    print(
    "GRAYLOG FILE NAME WAS NOT CHANGED."
)

    return str(output_file)

# =========================================================
# RETURN TO GRAYLOG DASHBOARD
# =========================================================

def click_dashboards(page):

    print()
    print("========================================")
    print("CLICK TOP DASHBOARDS")
    print("========================================")

    print("Looking for the TOP Dashboards navigation link...")

    dashboards = page.get_by_text("Dashboards", exact=True)
    candidates = []

    for i in range(dashboards.count()):
        item = dashboards.nth(i)
        try:
            if not item.is_visible():
                continue
            box = item.bounding_box()
            if not box or box["y"] > 70:
                continue

            text = (item.inner_text() or "").strip()
            aria = (item.get_attribute("aria-label") or "").strip()
            title = (item.get_attribute("title") or "").strip()
            href = (item.get_attribute("href") or "").strip()

            print(
                f"TOP DASHBOARDS: text={text!r}, aria={aria!r}, "
                f"title={title!r}, href={href!r}, "
                f"x={box['x']:.0f}, y={box['y']:.0f}"
            )

            # Prefer an actual top navigation link/button.
            tag = (item.evaluate("el => el.tagName") or "").upper()
            candidates.append((0 if tag in ("A", "BUTTON") else 1, box["x"], item))
        except Exception as e:
            print(f"Dashboards {i} skipped: {e}")

    if not candidates:
        # Fallback: inspect top navigation anchors/buttons by accessible text.
        nav = page.locator('a, button, [role="button"]')
        for i in range(nav.count()):
            item = nav.nth(i)
            try:
                if not item.is_visible():
                    continue
                box = item.bounding_box()
                if not box or box["y"] > 70:
                    continue
                text = (item.inner_text() or "").strip()
                aria = (item.get_attribute("aria-label") or "").strip()
                title = (item.get_attribute("title") or "").strip()
                if text == "Dashboards" or aria == "Dashboards" or title == "Dashboards":
                    candidates.append((0, box["x"], item))
                    break
            except Exception:
                continue

    if not candidates:
        page.screenshot(path="dashboards_navigation_error.png", full_page=True)
        raise Exception('TOP "Dashboards" navigation button could not be found.')

    candidates.sort(key=lambda x: (x[0], x[1]))
    _, _, selected = candidates[0]

    print("FOUND TOP DASHBOARDS NAVIGATION.")
    selected.click(force=True)
    page.wait_for_timeout(3000)
    print("TOP DASHBOARDS CLICKED.")


# =========================================================
# # CLICK SOURCES DASHBOARD
# =========================================================

def click_source(page):

    print()
    print("========================================")
    print("# CLICK SOURCES DASHBOARDS DASHBOARD")
    print("========================================")

    # In the Dashboards list, the dashboard is named "Sources" (plural).
    # Do NOT search for/click a widget-level "Source" field.
    candidates = page.get_by_text("Sources", exact=True)

    for i in range(candidates.count()):
        item = candidates.nth(i)
        try:
            if not item.is_visible():
                continue

            box = item.bounding_box()
            if box:
                print(
                    f"Sources {i}: x={box['x']:.0f}, "
                    f"y={box['y']:.0f}, "
                    f"w={box['width']:.0f}, "
                    f"h={box['height']:.0f}"
                )

            # Prefer the dashboard title link/row.
            item.click(force=True)
            page.wait_for_timeout(3000)

            print("SOURCES DASHBOARD CLICKED.")
            return

        except Exception as e:
            print(f"Sources {i} skipped: {e}")

    # Fallback: inspect links/buttons containing the exact dashboard name.
    nav = page.locator('a, button, [role="button"]')
    for i in range(nav.count()):
        item = nav.nth(i)
        try:
            if not item.is_visible():
                continue
            box = item.bounding_box()
            if not box or box["y"] > 600:
                continue
            text = (item.inner_text() or "").strip()
            aria = (item.get_attribute("aria-label") or "").strip()
            title = (item.get_attribute("title") or "").strip()
            href = (item.get_attribute("href") or "").strip()

            if text == "Sources" or aria == "Sources" or title == "Sources":
                print(
                    f"FALLBACK SOURCES: text={text!r}, aria={aria!r}, "
                    f"title={title!r}, href={href!r}, "
                    f"x={box['x']:.0f}, y={box['y']:.0f}"
                )
                item.click(force=True)
                page.wait_for_timeout(3000)
                print("SOURCES DASHBOARD CLICKED.")
                return
        except Exception:
            continue

    page.screenshot(path="sources_dashboard_error.png", full_page=True)
    raise Exception('"Sources" dashboard could not be found.')


# =========================================================
# FIND SECOND WIDGET AND SELECT SAME TPA
# =========================================================

def select_tpa_in_total_plans_widget(page):

    print()
    print("========================================")
    print("FIND TOTAL PLANS PER TPA USER")
    print("========================================")

    graylog_tpa_name = get_graylog_tpa_name(TPA_NAME)

    title = page.get_by_text(
        "Total Plans Per TPA User",
        exact=True
    )

    title.wait_for(
        state="visible",
        timeout=30000
    )

    title_box = title.bounding_box()

    if not title_box:
        raise Exception(
            "Total Plans Per TPA User title position unavailable."
        )

    print("FOUND: Total Plans Per TPA User")
    print(
        f"Widget title: x={title_box['x']:.0f}, "
        f"y={title_box['y']:.0f}"
    )

    page.wait_for_timeout(1500)

    # -----------------------------------------------------
    # Find the widget/card containing the exact title.
    # -----------------------------------------------------
    widget = None
    current = title

    for level in range(8):
        try:
            current = current.locator("xpath=..")
            box = current.bounding_box()
            if not box:
                continue

            text = current.inner_text()

            if (
                graylog_tpa_name in text
                and box["width"] > 300
                and box["height"] > 80
            ):
                widget = current
                print(
                    f"FOUND TOTAL PLANS WIDGET CONTAINER "
                    f"(level {level + 1}): "
                    f"x={box['x']:.0f}, y={box['y']:.0f}, "
                    f"w={box['width']:.0f}, h={box['height']:.0f}"
                )
                break
        except Exception:
            pass

    # -----------------------------------------------------
    # Search only inside that widget for the SAME Graylog TPA.
    # Accept both:
    #   Benefit Plans Plus LLC
    #   /Benefit Plans Plus LLC
    # -----------------------------------------------------
    candidates = []

    if widget is not None:
        candidates.extend([
            widget.get_by_text(graylog_tpa_name, exact=True),
            widget.get_by_text(f"/{graylog_tpa_name}", exact=True),
        ])
    else:
        # Fallback: all exact Graylog TPA text, then choose the one
        # closest below the Total Plans Per TPA User title.
        candidates.extend([
            page.get_by_text(graylog_tpa_name, exact=True),
            page.get_by_text(f"/{graylog_tpa_name}", exact=True),
        ])

    found = []

    for locator in candidates:
        try:
            for i in range(locator.count()):
                item = locator.nth(i)

                if not item.is_visible():
                    continue

                box = item.bounding_box()
                if not box:
                    continue

                # Ignore text outside the second widget when using
                # the fallback page-wide search.
                if widget is None:
                    if box["y"] < title_box["y"]:
                        continue

                    distance = abs(box["y"] - title_box["y"])
                else:
                    distance = abs(box["y"] - title_box["y"])

                text = (item.inner_text() or "").strip()

                print(
                    f"TPA candidate: text={text!r}, "
                    f"x={box['x']:.0f}, y={box['y']:.0f}, "
                    f"distance={distance:.0f}"
                )

                found.append((distance, box["y"], item))

        except Exception as e:
            print(f"TPA candidate skipped: {e}")

    if not found:
        page.screenshot(
            path="total_plans_tpa_error.png",
            full_page=True
        )
        raise Exception(
            f'Could not find same TPA "{graylog_tpa_name}" in Total Plans Per TPA User.'
        )

    # Closest visible TPA belonging to the widget.
    found.sort(key=lambda x: (x[0], x[1]))
    _, _, selected_tpa = found[0]

    selected_box = selected_tpa.bounding_box()

    print()
    print("FOUND SAME TPA IN TOTAL PLANS PER TPA USER.")

    if selected_box:
        print(
            f"Selected TPA position: "
            f"x={selected_box['x']:.0f}, "
            f"y={selected_box['y']:.0f}, "
            f"w={selected_box['width']:.0f}, "
            f"h={selected_box['height']:.0f}"
        )

    print("CLICKING SAME TPA...")

    selected_tpa.scroll_into_view_if_needed()
    selected_tpa.click(force=True)

    page.wait_for_timeout(2000)

    print("SAME TPA CLICKED IN TOTAL PLANS PER TPA USER.")

    # -----------------------------------------------------
    # CLICK: Show documents for value
    # -----------------------------------------------------
    print()
    print("========================================")
    print("CLICK SHOW DOCUMENTS FOR VALUE")
    print("========================================")

    show_documents = page.get_by_text(
        "Show documents for value",
        exact=True
    )

    selected_show_documents = None

    for i in range(show_documents.count()):
        try:
            item = show_documents.nth(i)

            if not item.is_visible():
                continue

            box = item.bounding_box()
            if box:
                print(
                    f"Show documents {i}: "
                    f"x={box['x']:.0f}, y={box['y']:.0f}, "
                    f"w={box['width']:.0f}, h={box['height']:.0f}"
                )

            selected_show_documents = item
            break

        except Exception as e:
            print(f"Show documents {i} skipped: {e}")

    if selected_show_documents is None:
        page.screenshot(
            path="total_plans_show_documents_error.png",
            full_page=True
        )
        raise Exception(
            '"Show documents for value" could not be found after selecting the TPA.'
        )

    print("FOUND: Show documents for value")
    print("CLICKING SHOW DOCUMENTS FOR VALUE...")

    selected_show_documents.click(force=True)
    page.wait_for_timeout(2500)

    print("SHOW DOCUMENTS FOR VALUE CLICKED.")


# =========================================================
# HOVER SECOND MESSAGES WIDGET + CLICK EDIT
# =========================================================

def edit_total_plans_messages_widget(page):

    print()
    print("========================================")
    print("HOVER MESSAGES WIDGET AND CLICK EDIT")
    print("========================================")

    # After "Show documents for value", Graylog opens a
    # Messages widget similar to the one shown in the screenshot:
    # Messages for GROUPS:"<TPA>"
    #
    # We find that widget by its title, hover it, then click
    # the Edit icon in the widget header.

    title_candidates = [
        page.get_by_text(
            f'Messages for GROUPS:"{TPA_NAME}"',
            exact=True
        ),
        page.get_by_text(
            f'Messages for GROUPS:"/{TPA_NAME}"',
            exact=True
        ),
        page.locator(
            'text=/^Messages for GROUPS:.*InWest Retirement Solutions.*$/i'
        )
    ]

    titles = []
    seen = set()

    for locator in title_candidates:
        for i in range(locator.count()):
            try:
                item = locator.nth(i)
                if not item.is_visible():
                    continue
                box = item.bounding_box()
                if not box:
                    continue
                key = (round(box["x"], 1), round(box["y"], 1), item.inner_text().strip())
                if key in seen:
                    continue
                seen.add(key)
                titles.append((item, box))
            except Exception:
                pass

    if not titles:
        page.screenshot(
            path="total_plans_messages_widget_error.png",
            full_page=True
        )
        raise Exception(
            f'Messages widget for TPA "{TPA_NAME}" could not be found.'
        )

    # Prefer the lower/most recently opened Messages widget.
    message_title, title_box = max(
        titles,
        key=lambda x: x[1]["y"]
    )

    print(
        f'Messages widget found: text={message_title.inner_text().strip()!r}, '
        f'x={title_box["x"]:.0f}, y={title_box["y"]:.0f}'
    )

    # Move cursor over the Messages widget title/header.
    message_title.hover()
    page.wait_for_timeout(1800)

    print("Cursor moved over Messages widget.")

    # Find visible Edit controls. Graylog exposes the icon through
    # title/aria-label. Choose the Edit control aligned with the
    # Messages widget header.
    edits = page.locator(
        'button[title="Edit"], '
        'button[aria-label="Edit"], '
        '[data-original-title="Edit"]'
    )

    best = None
    best_score = None

    for i in range(edits.count()):
        try:
            edit = edits.nth(i)
            if not edit.is_visible():
                continue

            box = edit.bounding_box()
            if not box:
                continue

            # Header should be close to the title's y position,
            # and normally on the right side of the widget.
            y_distance = abs(box["y"] - title_box["y"])

            print(
                f"Edit {i}: x={box['x']:.0f}, y={box['y']:.0f}, "
                f"distance={y_distance:.0f}"
            )

            if y_distance > 90:
                continue

            # Prefer controls to the right of the title.
            right_penalty = 0 if box["x"] >= title_box["x"] else 10000
            score = (right_penalty + y_distance, -box["x"])

            if best_score is None or score < best_score:
                best = edit
                best_score = score

        except Exception:
            pass

    if best is None:
        page.screenshot(
            path="total_plans_messages_edit_error.png",
            full_page=True
        )
        raise Exception(
            "Edit symbol for the Total Plans Messages widget could not be found."
        )

    best_box = best.bounding_box()

    if best_box:
        print(
            f"FOUND EDIT SYMBOL: x={best_box['x']:.0f}, "
            f"y={best_box['y']:.0f}, "
            f"w={best_box['width']:.0f}, h={best_box['height']:.0f}"
        )

    print("CLICKING EDIT SYMBOL...")

    best.click(force=True)
    page.wait_for_timeout(2500)

    print("MESSAGES WIDGET EDITOR OPENED SUCCESSFULLY.")


# =========================================================
# ADD EXPORT FIELD IN MESSAGE TABLE EXPORT POPUP
# =========================================================
def add_message_export_field(page, field_name):

    print()
    print("----------------------------------------")
    print(f'ADDING EXPORT FIELD: {field_name}')
    print("----------------------------------------")

    placeholders = page.locator(
        'div[id$="-placeholder"]'
    ).filter(
        has_text="Add a field"
    )

    selected = None

    for i in range(placeholders.count()):
        try:
            item = placeholders.nth(i)
            if not item.is_visible():
                continue

            box = item.bounding_box()
            if not box:
                continue

            # The export popup is centered/right side of the page.
            if box["x"] > 500 and box["y"] > 250:
                selected = item
                print(
                    f'FOUND Add a field for {field_name}: '
                    f'x={box["x"]:.0f}, y={box["y"]:.0f}'
                )
                break
        except Exception:
            pass

    if selected is None:
        page.screenshot(
            path=f"export_add_field_{field_name}_error.png",
            full_page=True
        )
        raise Exception(
            f'Add a field control not found for {field_name}.'
        )

    control = selected.locator("xpath=../..")
    control.click(force=True)
    page.wait_for_timeout(500)

    # React-Select input.
    inputs = page.locator("input")
    input_box = None
    field_input = None

    for i in range(inputs.count()):
        try:
            item = inputs.nth(i)
            if not item.is_visible():
                continue

            box = item.bounding_box()
            if not box:
                continue

            # Dropdown search input is normally near the export popup's
            # Add a field control and is a very small/short input.
            if box["x"] > 500 and box["y"] > 300:
                field_input = item
                input_box = box
                break
        except Exception:
            pass

    if field_input is None:
        page.screenshot(
            path=f"export_field_input_{field_name}_error.png",
            full_page=True
        )
        raise Exception(
            f'Field selector input not found for {field_name}.'
        )

    print(
        f'TYPING {field_name}: '
        f'x={input_box["x"]:.0f}, y={input_box["y"]:.0f}'
    )

    field_input.fill(field_name)
    page.wait_for_timeout(800)

    # Select the exact matching React-Select option.
    options = page.locator('[role="option"]')
    selected_option = None

    for i in range(options.count()):
        try:
            option = options.nth(i)
            if not option.is_visible():
                continue

            text = option.inner_text().strip()
            lines = [
                line.strip()
                for line in text.splitlines()
                if line.strip()
            ]

            if any(line.lower() == field_name.lower() for line in lines):
                selected_option = option
                box = option.bounding_box()
                print(
                    f'FOUND OPTION: {text!r}'
                    + (
                        f' x={box["x"]:.0f}, y={box["y"]:.0f}'
                        if box else ""
                    )
                )
                break
        except Exception:
            pass

    if selected_option is None:
        # Fallback: click an option whose complete text contains the field name.
        for i in range(options.count()):
            try:
                option = options.nth(i)
                if not option.is_visible():
                    continue
                if field_name.lower() in option.inner_text().strip().lower():
                    selected_option = option
                    break
            except Exception:
                pass

    if selected_option is None:
        page.screenshot(
            path=f"export_field_option_{field_name}_error.png",
            full_page=True
        )
        raise Exception(
            f'Export field option {field_name} could not be found.'
        )

    print(f'SELECTING {field_name}...')
    selected_option.click(force=True)
    page.wait_for_timeout(800)
    print(f'{field_name} ADDED SUCCESSFULLY.')


# =========================================================
# HOVER TOTAL PLANS MESSAGES + CLICK FIRST DOWNLOAD ICON
# =========================================================
def download_total_plans_messages_csv(page):

    print()
    print("========================================")
    print("HOVER TOTAL PLANS MESSAGES AND CLICK FIRST DOWNLOAD ICON")
    print("========================================")

    message_title = find_messages_widget_title_for_tpa(
        page,
        TPA_NAME
    )

    title_box = message_title.bounding_box()
    if not title_box:
        raise Exception(
            "Messages widget title position unavailable."
        )

    title_text = message_title.inner_text().strip()

    print(
        f'Messages widget found: text={title_text!r}, '
        f'x={title_box["x"]:.0f}, y={title_box["y"]:.0f}'
    )

    widget = message_title.locator("xpath=ancestor::*[.//button][1]")
    widget_box = None
    try:
        widget_box = widget.bounding_box()
    except Exception:
        pass

    if not widget_box or widget_box["width"] < 500:
        for levels in range(1, 7):
            try:
                candidate = message_title
                for _ in range(levels):
                    candidate = candidate.locator("xpath=..")
                box = candidate.bounding_box()
                if box and box["width"] > 700 and box["height"] > 150:
                    widget = candidate
                    widget_box = box
                    break
            except Exception:
                pass

    if not widget_box:
        raise Exception("Could not determine Total Plans Messages widget bounds.")

    hover_x = widget_box["x"] + widget_box["width"] / 2
    hover_y = title_box["y"]

    print(
        f"Moving cursor over Messages widget: x={hover_x:.0f}, y={hover_y:.0f}"
    )
    page.mouse.move(hover_x, hover_y)
    page.wait_for_timeout(1800)

    print("Cursor moved over Messages widget.")
    print()
    print("SEARCHING FOR FIRST DOWNLOAD SYMBOL...")

    candidates = []
    selectors = [
        'button[aria-label]',
        'button[title]',
        '[role="button"][aria-label]',
        '[role="button"][title]',
    ]

    for selector in selectors:
        locator = widget.locator(selector)
        for i in range(locator.count()):
            try:
                item = locator.nth(i)
                if not item.is_visible():
                    continue
                box = item.bounding_box()
                if not box:
                    continue

                aria = (awaitable_attr(item, "aria-label") or "").strip()
                title = (awaitable_attr(item, "title") or "").strip()
                label = aria or title

                if label.lower() in {
                    "edit",
                    "open actions dropdown",
                    "compress width",
                    "focus this widget",
                }:
                    continue

                if label.lower() == "export all search results":
                    candidates.append((item, box, label, 0))
                    continue

                if (
                    box["y"] >= title_box["y"] - 15
                    and box["y"] <= title_box["y"] + 45
                    and box["x"] > title_box["x"] + 300
                    and box["width"] <= 45
                    and box["height"] <= 45
                ):
                    candidates.append((item, box, label, 1))
            except Exception:
                pass

    if not candidates:
        page.screenshot(
            path="total_plans_first_download_icon_error.png",
            full_page=True
        )
        raise Exception(
            "First download symbol for Total Plans Messages widget could not be found."
        )

    explicit = [c for c in candidates if c[3] == 0]
    if explicit:
        chosen = min(explicit, key=lambda c: c[1]["x"])
    else:
        chosen = min(candidates, key=lambda c: c[1]["x"])

    button, box, label, _ = chosen

    print(
        f"FIRST DOWNLOAD SYMBOL FOUND: text={label!r}, "
        f"x={box['x']:.0f}, y={box['y']:.0f}, "
        f"w={box['width']:.0f}, h={box['height']:.0f}"
    )

    print("CLICKING FIRST DOWNLOAD SYMBOL...")
    button.click(force=True)
    page.wait_for_timeout(1500)

    print("DOWNLOAD SYMBOL CLICKED.")
    print("Waiting for export message table search results popup...")

    popup_title = page.get_by_text(
        "Export message table search results",
        exact=True
    )

    popup_title.first.wait_for(
        state="visible",
        timeout=10000
    )

    print("EXPORT MESSAGE TABLE SEARCH RESULTS POPUP OPENED.")

    # =====================================================
    # ADD USER_NAME FIRST
    # =====================================================
    add_message_export_field(page, "USER_NAME")

    # =====================================================
    # ADD PLAN_CATEGORY SECOND
    # =====================================================
    add_message_export_field(page, "PLAN_CATEGORY")

    print()
    print("BOTH EXPORT FIELDS ADDED SUCCESSFULLY.")
    print("USER_NAME")
    print("PLAN_CATEGORY")

    # =====================================================
    # START DOWNLOAD ONLY AFTER BOTH FIELDS ARE ADDED
    # =====================================================
    print()
    print("FINDING BLUE START DOWNLOAD BUTTON...")

    start_buttons = page.get_by_role(
        "button",
        name="Start Download",
        exact=True
    )

    start_button = None
    for i in range(start_buttons.count()):
        try:
            item = start_buttons.nth(i)
            if item.is_visible():
                start_button = item
                break
        except Exception:
            pass

    if start_button is None:
        page.screenshot(
            path="total_plans_start_download_error.png",
            full_page=True
        )
        raise Exception("Start Download button could not be found.")

    print()
    print("FOUND BLUE START DOWNLOAD BUTTON.")
    print("CLICKING START DOWNLOAD...")

    # The export API response is only an export identifier, not the CSV body.
    # Wait for the actual browser download that Graylog starts afterward.
    with page.expect_download(timeout=120000) as download_info:
        start_button.click(force=True)

    download = download_info.value
    original_filename = download.suggested_filename

    print()
    print("BROWSER DOWNLOAD RECEIVED.")
    print("GRAYLOG ORIGINAL FILENAME:")
    print(original_filename)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    output_file = OUTPUT_DIR / original_filename

    print()
    print("SAVING TO:")
    print(output_file.resolve())

    download.save_as(str(output_file))

    print()
    print("SECOND CSV DOWNLOAD COMPLETED.")
    print("SAVED TO:")
    print(output_file)
    print("GRAYLOG FILE NAME WAS NOT CHANGED.")

    return original_filename

# =========================================================
# SMALL HELPER FOR ARIA/TITLE ATTRIBUTES
# =========================================================
def awaitable_attr(item, name):
    try:
        return item.get_attribute(name)
    except Exception:
        return None


# =========================================================
# MAIN
# =========================================================


# =========================================================
# UI ENTRY POINT
# =========================================================
def run_graylog_automation(tpa_name):
    """Run the complete Graylog automation for the TPA selected in the UI."""
    global TPA_NAME, OUTPUT_DIR

    if not tpa_name or not str(tpa_name).strip():
        raise ValueError("TPA name is required.")

    TPA_NAME = str(tpa_name).strip()

    OUTPUT_DIR = (
        Path.home()
        / "Desktop"
        / "graylog_outputs"
        / TPA_NAME
    )

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    with sync_playwright() as p:

        browser = p.chromium.launch(
            headless=True,
            channel="chromium"
        )

        context = browser.new_context(
            accept_downloads=True,
            viewport={
                "width": 1600,
                "height": 1000
            }
        )

        page = context.new_page()

        try:

            # =================================================
            # STEP 1
            # =================================================

            print()
            print("========================================")
            print("STEP 1 - OPENING GRAYLOG")
            print("========================================")

            page.goto(
                GRAYLOG_URL,
                wait_until="domcontentloaded",
                timeout=60000
            )

            page.wait_for_timeout(
                3000
            )

            print(
                "Graylog page opened."
            )


            # =================================================
            # STEP 2
            # =================================================

            print()
            print("========================================")
            print("STEP 2 - LOGIN")
            print("========================================")

            username_login = page.locator(
                'input[name="username"], '
                'input[placeholder*="Username" i], '
                'input[placeholder*="username" i], '
                'input[type="email"]'
            ).first

            password_login = page.locator(
                'input[name="password"], '
                'input[type="password"], '
                'input[placeholder*="Password" i]'
            ).first

            if username_login.is_visible():

                username_login.fill(
                    GRAYLOG_USERNAME
                )

            if password_login.is_visible():

                password_login.fill(
                    GRAYLOG_PASSWORD
                )

            login_button = page.locator(
                'button:has-text("Sign in"), '
                'button:has-text("Login"), '
                'button:has-text("Log in"), '
                'input[type="submit"]'
            ).first

            if login_button.is_visible():

                login_button.click()

            page.wait_for_timeout(
                4000
            )

            print(
                "Graylog login completed."
            )


            # =================================================
            # STEP 3 - REOPEN GRAYLOG DASHBOARD
            # =================================================

            print()
            print("========================================")
            print("STEP 3 - REOPENING GRAYLOG DASHBOARD")
            print("========================================")

            page.goto(
                GRAYLOG_URL,
                wait_until="domcontentloaded",
                timeout=60000
            )

            page.wait_for_timeout(
                5000
            )

            print(
                "Graylog dashboard opened again."
            )

            # Wait until the first dashboard widget is visible.
            first_widget = page.get_by_text(
                "Total Login Count Per TPA/User",
                exact=True
            )

            first_widget.wait_for(
                state="visible",
                timeout=30000
            )

            print(
                "FOUND: Total Login Count Per TPA/User"
            )


            # =================================================
            # STEP 4
            # =================================================

            print()
            print("========================================")
            print("STEP 4 - SELECT TPA")
            print("========================================")

            graylog_tpa_name = get_graylog_tpa_name(TPA_NAME)

            print(
                f"UI TPA: {TPA_NAME}"
            )
            print(
                f"Graylog TPA: {graylog_tpa_name}"
            )

            # Graylog can display a TPA either with or without a leading slash.
            # The UI label and Graylog label can also differ.
            tpa_values = []

            for value in [
                f"/{graylog_tpa_name}",
                graylog_tpa_name,
                f"/{TPA_NAME}",
                TPA_NAME
            ]:
                if value and value not in tpa_values:
                    tpa_values.append(value)

            tpa = None
            found_value = None
            deadline = 20_000
            waited = 0

            while waited < deadline and tpa is None:

                for value in tpa_values:

                    try:

                        candidate = page.get_by_text(
                            value,
                            exact=True
                        )

                        for i in range(candidate.count()):

                            item = candidate.nth(i)

                            if not item.is_visible():
                                continue

                            box = item.bounding_box()

                            if not box:
                                continue

                            tpa = item
                            found_value = value
                            break

                        if tpa is not None:
                            break

                    except Exception:
                        pass

                if tpa is not None:
                    break

                page.wait_for_timeout(500)
                waited += 500

            if tpa is None:

                try:
                    visible_text = page.locator("body").inner_text()
                    print()
                    print("VISIBLE DASHBOARD TEXT (TPA SEARCH FAILED):")
                    print(visible_text[:12000])
                except Exception:
                    pass

                page.screenshot(
                    path="tpa_selection_error.png",
                    full_page=True
                )

                raise Exception(
                    f'Could not find visible Graylog TPA "{graylog_tpa_name}" '
                    f'for UI TPA "{TPA_NAME}".'
                )

            found_text = (
                tpa.inner_text().strip()
            )

            print(
                f"FOUND TPA: {found_text!r}"
            )
            print(
                f"Matched locator value: {found_value!r}"
            )

            print(
                "Clicking TPA..."
            )

            tpa.scroll_into_view_if_needed()

            tpa.click(
                force=True
            )

            page.wait_for_timeout(
                1500
            )

            print(
                "TPA clicked."
            )

            # =================================================
            # STEP 5
            # =================================================

            print()
            print("========================================")
            print("STEP 5 - SHOW DOCUMENTS")
            print("========================================")

            show_documents = page.get_by_text(
                "Show documents for value",
                exact=True
            )

            show_documents.wait_for(
                state="visible",
                timeout=15000
            )

            print(
                "FOUND: Show documents for value"
            )

            show_documents.click()

            page.wait_for_timeout(
                2500
            )

            print(
                "Clicked: Show documents for value"
            )


            # =================================================
            # STEP 6
            # =================================================

            print()
            print("========================================")
            print("STEP 6 - MESSAGES WIDGET")
            print("========================================")

            message_title = find_messages_widget_title_for_tpa(
                page,
                TPA_NAME
            )

            print(
                "FOUND CORRECT MESSAGE WIDGET"
            )


            # =================================================
            # STEP 7
            # =================================================

            login_edit = find_login_message_edit(
                page,
                message_title
            )

            print(
                "Clicking Messages Edit..."
            )

            login_edit.click(
                force=True
            )

            page.wait_for_timeout(
                2500
            )

            print(
                "Edit screen opened."
            )


            # =================================================
            # STEP 8
            # =================================================

            query = copy_login_query(
                page
            )


            # =================================================
            # STEP 9
            # =================================================

            open_search(
                page
            )


            # =================================================
            # STEP 10
            # =================================================

            paste_query(
                page,
                query
            )


            # =================================================
            # STEP 11
            # =================================================

            execute_search(
                page
            )


            # =================================================
            # STEP 12
            # =================================================

            click_black_triangle(
                page
            )


            # =================================================
            # STEP 13
            # =================================================

            select_all_messages(
                page
            )


            # =================================================
            # STEP 14
            # =================================================

            edit_all_messages(
                page
            )


            # =================================================
            # STEP 15
            # =================================================

            click_add_field(
                page
            )


            # =================================================
            # STEP 16
            # =================================================

            type_username(
                page
            )


            # =================================================
            # STEP 17
            # =================================================

            select_username(
                page
            )


            # =================================================
            # STEP 18
            # =================================================

            verify_username_added(
                page
            )

            # =================================================
            # STEP 18A - ADD GROUPS FIELD
            # =================================================

            print()
            print("========================================")
            print("ADDING GROUPS FIELD")
            print("========================================")

            click_add_field(
                page
            )

            type_groups(
                page
            )

            select_groups(
                page
            )

            verify_groups_added(
                page
            )

            # =================================================
            # STEP 18B - SCROLL LEFT EDITOR PANEL TO BOTTOM
            # =================================================

            scroll_left_editor_to_bottom(
                page
            )

            # =================================================
            # STEP 19 - CLICK UPDATE WIDGET
            # =================================================

            click_update_widget(
                page
            )

            # =================================================
            # STEP 20 - HOVER AND DOWNLOAD CSV
            # =================================================
            download_all_messages_csv(
                page
            )


            # =================================================
            # SUCCESS
            # =================================================

            print()
            print("========================================")
            print("SUCCESS")
            print("========================================")

            print()
            print(
                "TPA:",
                TPA_NAME
            )

            print()
            print(
                "QUERY:"
            )

            print(
                query
            )

            print()
            print(
                "COMPLETED:"
            )

            print(
                "1. Selected TPA"
            )

            print(
                "2. Show documents for value"
            )

            print(
                "3. Opened Messages widget"
            )

            print(
                "4. Copied ONLY User logged in query"
            )

            print(
                "5. Opened Search"
            )

            print(
                "6. Pasted query"
            )

            print(
                "7. Clicked black ▼"
            )

            print(
                "8. Selected All messages"
            )

            print(
                "9. Hovered All Messages"
            )

            print(
                "10. Clicked top-right Edit"
            )

            print(
                "11. Clicked Add a field"
            )

            print(
                '12. Typed "username"'
            )

            print(
                '13. Selected lowercase "username"'
            )

            print(
                '14. Typed "GROUPS"'
            )

            print(
                '15. Selected "GROUPS"'
            )

            print()
            print(
                "USERNAME + GROUPS FIELDS ADDED."
            )

            print()
            print(
                "FIRST CSV DOWNLOAD COMPLETED."
            )


            # =================================================
            # STEP 21 - CLICK DASHBOARDS
            # =================================================
            click_dashboards(page)


            # =================================================
            # STEP 22 - # CLICK SOURCES DASHBOARD
            # =================================================
            click_source(page)


            # =================================================
            # STEP 22A - USE ALL MESSAGES FOR THE DASHBOARD
            # =================================================
            # The first CSV explicitly uses the All messages range. Apply
            # the same range to the dashboard before opening its TPA results,
            # otherwise Show documents can export only the dashboard's
            # default time window (often yielding a header-only CSV).
            click_black_triangle(page)
            select_all_messages(page)


            # =================================================
            # STEP 23 - TOTAL PLANS PER TPA USER
            # =================================================
            select_tpa_in_total_plans_widget(page)


            # =================================================
            # STEP 24 - HOVER MESSAGES AND CLICK FIRST DOWNLOAD SYMBOL
            # =================================================
            download_total_plans_messages_csv(page)


            print()
            print("========================================")
            print("STEP 2 READY")
            print("========================================")
            print()
            print("Total Plans Per TPA User opened.")
            print("Show documents for value clicked.")
            print(f"Same TPA selected in Graylog: /{get_graylog_tpa_name(TPA_NAME)}")
            print("Hovered Messages widget.")
            print("Clicked FIRST download symbol.")
            print("Second CSV download completed.")
            print()


            return {
                "status": "success",
                "tpa": TPA_NAME,
                "output_folder": str(OUTPUT_DIR.resolve()),
                "message": "Graylog automation completed successfully."
            }

        except Exception as e:

            print()
            print("========================================")
            print("ERROR")
            print("========================================")

            print(
                str(e)
            )

            try:

                page.screenshot(
                    path="graylog_error.png",
                    full_page=True
                )

                print()
                print(
                    "Screenshot saved: graylog_error.png"
                )

            except:
                pass

            raise

        finally:

            browser.close()


if __name__ == "__main__":
    # Standalone test. Flask imports the module and calls run_graylog_automation().
    run_graylog_automation("InWest Retirement Solutions")
