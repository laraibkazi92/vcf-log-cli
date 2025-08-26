def FalsePositives(service):
    if service == "lcm":
        return ["Unsupported product type",
                         "Failed to decode jwt token",
                         "Error decoding JWT token",
                         "Unknown exception while parsing jwt token",
                         "Can't find resource for bundle java.util.PropertyResourceBundle",
                         "Default PSC id",
                         "Resource type is unknown",
                         "Failed to decode username from request headers",
                         "Failed to get resource name for",
                         "All Edge Transport Nodes",
                         "logical inventory - get ESXi host failed for ESXi host",
                         "An unexpected error occurred while masking sensitive data"
                         ]
    if service == "domainmanager":
        return ["Error decoding JWT token",
                "Failed to decode jwt token JWT",
                "Allowed clock skew",
                "Unknown exception while parsing jwt token",
                "An unexpected error occurred while masking sensitive data",
                "Skipping strechcluster metrics collection"
                                   ]
                                   

    if service == "operationsmanager":
        return ["Can't find resource for bundle java.util.PropertyResourceBundle",
                                       "null",
                                       "Signature validation failed JWT signature",
                                       "JWT validity cannot be asserted and should not be trusted",
                                       "Error decoding JWT token",
                                       "Unknown exception while parsing jwt token JWT",
                                       "JWT expired at",
                                       "Failed to decode jwt",
                                       "Unable to fetch upgrades",
                                       "An unexpected error occurred while masking sensitive data"
                                       ]
    
    if service == "commonsvcs":
        return ["unexpected workflow status value: CANCELLED"]

    if service == "sddc-manager-ui-app":
        return []