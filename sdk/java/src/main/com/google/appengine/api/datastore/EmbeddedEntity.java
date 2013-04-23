// Copyright 2012 Google Inc. All Rights Reserved.

package com.google.appengine.api.datastore;

import com.google.common.base.Objects;

import java.util.HashMap;
import java.util.Map;

/**
 * A property value containing embedded entity properties (and optionally a {@link Key}).
 *
 * This class is similar to {@link Entity}, but differs in the following ways:
 * <ul>
 * <li>{@link #equals(Object)} and {@link #hashCode()} compare the embedded
 * properties in addition to the {@link Key}.
 * <li>It is not queryable when stored in the datastore.
 * <li>A {@link Key} is optional.
 * <li>{@link Key Keys} without a name or id are considered equal if all other
 * aspects of the keys are equal (as they will not be assigned IDs by the
 * datastore when embedded).
 * </ul>
 *
 * To convert from an {@link Entity} use:
 * <pre> {@code
 * EmbeddedEntity sv = new EmbeddedEntity();
 * sv.setKey(entity.getKey())
 * sv.setPropertiesFrom(entity)
 * }</pre>
 * To convert to an {@link Entity} use:
 * <pre> {@code
 * Entity entity = new Entity(sv.getKey())
 * entity.setPropertiesFrom(sv);
 * }</pre>
 *
 */
public final class EmbeddedEntity extends PropertyContainer {
  private Key key = null;
  private final Map<String, Object> propertyMap = new HashMap<String, Object>();

  /**
   * @return the key or {@code null}.
   */
  public Key getKey() {
    return key;
  }

  /**
   * @param key the key to set
   */
  public void setKey( Key key) {
    this.key = key;
  }

  @Override
  Map<String, Object> getPropertyMap() {
    return propertyMap;
  }

  @Override
  public EmbeddedEntity clone() {
    EmbeddedEntity result = new EmbeddedEntity();
    result.setKey(key);
    result.setPropertiesFrom(this);
    return result;
  }

  @Override
  public String toString() {
    StringBuilder builder = new StringBuilder("<EmbeddedEntity");
    if (key != null) {
      builder.append(" [").append(key).append(']');
    }
    builder.append(":\n");
    appendPropertiesTo(builder);
    builder.append(">\n");
    return builder.toString();
  }

  @Override
  public int hashCode() {
    return Objects.hashCode(key, propertyMap);
  }

  @Override
  public boolean equals(Object obj) {
    if (this == obj) return true;
    if (!(obj instanceof EmbeddedEntity)) return false;
    EmbeddedEntity other = (EmbeddedEntity) obj;
    if (!propertyMap.equals(other.propertyMap)) return false;
    return key == null ? other.key == null : key.equals(other.key, false);
  }
}
