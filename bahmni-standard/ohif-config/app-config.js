window.config = {
  routerBasename: "/ohif",
  maxNumberOfWebWorkers: 4,
  defaultDataSourceName: "dicomweb",
  showStudyList: false,

  dataSources: [
    {
      namespace: "@ohif/extension-default.dataSourcesModule.dicomweb",
      sourceName: "dicomweb",
      configuration: {
        friendlyName: "DCM4CHEE5 PACS",
        name: "DCM4CHEE",

        wadoUriRoot: "/dcm4chee-arc/aets/DCM4CHEE/wado",
        qidoRoot: "/dcm4chee-arc/aets/DCM4CHEE/rs",
        wadoRoot: "/dcm4chee-arc/aets/DCM4CHEE/rs",

        qidoSupportsIncludeField: false,
        imageRendering: "wadors",
        thumbnailRendering: "wadors",
        enableStudyLazyLoad: true,
        supportsFuzzyMatching: true,
        supportsWildcard: true,
        omitQuotationForMultipartRequest: true,
      },
    },
  ],

  customizationService: [
    "@ohif/extension-default.customizationModule.multimonitor",
  ],

  multimonitor: [
    {
      id: "secondary",
      test: ({ multimonitor }) => multimonitor === "secondary",
      screens: [
        {
          id: "ohif1",
          screen: 1,
          location: {
            width: 1,
            height: 1,
            left: 0,
            top: 0,
          },
          options:
            "fullscreen=yes,location=no,menubar=no,scrollbars=no,status=no,titlebar=no",
        },
      ],
    },
  ],

  extensions: [],
  modes: [],

  defaultViewport: {
    viewportType: "stack",
  },
};
