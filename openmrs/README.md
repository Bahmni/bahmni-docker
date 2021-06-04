### Why does the repository contain binaries for modules?

This is for the time being while we are putting things together for a docker
based Bahmni distro. The binaries will be replaced with a reference to a build artefact
in a future story.

### Why are there different modules folders?

* `resources/modules` contains most modules needed for Bahmni
* `resources/modules-legacyui` contains different versions of the legacy UI module
* `resources/modules-pending` contains modules that are also needed for Bahmni

The modules in `resources/modules-pending` are
* `bahmnicore-0.93-SNAPSHOT.omod` - this module interferes with the OpenMRS legacy UI
* `openelis-atomfeed-client-0.93-SNAPSHOT.omod` - this module is not needed until OpenElis is
added to the Bahmni Docker distribution.
