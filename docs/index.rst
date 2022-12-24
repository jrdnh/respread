**********************
respread documentation
**********************

:mod:`respread` is a spreadsheet alternative for end-user models. It allows users to easily build a final modeling engine that can access Python's entire statistical, computational, and networking ecosystem.

* **Leverage the full Python ecosystem**
    - Integrate statistical or AI/ML components directly into the end-user model
    - Connect to resources over the web, such as data science models, third-party data vendors, or internal corporate datastores
    - Analyze datasets that are too big or not appropriately structured for spreadsheets
* **Create reusable, test-hardened components**
* **Quickly build end-user models as part of an automated process**

The library organizes functions into composite hierarchies that can be reused, tested, and configured at runtime. It allows users to work with elements of the hierarchy using regular class definitions and attribute access while automatically handling things like updates to the tree structure, cache management, and annotations/autocompletion integration.

|

.. _cards-clickable:

.. grid:: 1 2 2 2

   .. grid-item-card:: User guide
      :link: user_guide
      :link-type: ref
      :img-top: _static/user-guide.svg

      Jump in with the **Getting started** guide or review key concepts in depth.

   .. grid-item-card:: API reference
      :link: api_reference
      :link-type: ref
      :img-top: _static/api-reference.svg

      Detailed information on ``respread`` classes and methods.

|

.. toctree::
   :maxdepth: 2
   :hidden:

   user_guide/index
   api_reference/index
