### Why are there different modules folders?

* `resources/modules` contains all modules needed for Bahmni
* `resources/modules-1` contains the legacy UI module only

When running OpenMRS with all modules, the legacy UI module does not work,
hence the variant with the legacy UI module only.

This issue needs to be resolved in https://bahmni.atlassian.net/browse/BDI-2.

### Why does the repository contain binaries for modules?

This is for the time being while we are putting things together for a docker
based Bahmni distro. The binaries will be replaced with a reference to a build artefact
in a future story.
